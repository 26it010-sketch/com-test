from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.documents import pdf_response
from app.db.session import get_db
from app.dependencies.permissions import require_admin
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentAdminOut
from app.schemas.user import UserAdminOut, UserOut, UserStatusUpdate
from app.services import document_service as svc

# Every route in this router requires an admin, enforced server-side via the router dependency.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserAdminOut])
def list_users(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
               db: Session = Depends(get_db)):
    stmt = (select(User, func.count(Document.id))
            .outerjoin(Document, Document.owner_id == User.id)
            .group_by(User.id).order_by(User.created_at.desc(), User.id.desc())
            .offset(skip).limit(limit))
    out = []
    for user, count in db.execute(stmt):
        item = UserAdminOut.model_validate(user)
        item.document_count = count
        out.append(item)
    return out


@router.patch("/users/{user_id}", response_model=UserOut)
def set_user_status(user_id: int, body: UserStatusUpdate, db: Session = Depends(get_db),
                    admin: User = Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You cannot change your own status")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/documents", response_model=list[DocumentAdminOut])
def list_all_documents(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                       owner_id: int | None = None, db: Session = Depends(get_db)):
    return svc.list_all_documents(db, skip, limit, owner_id)


@router.get("/users/{user_id}/documents", response_model=list[DocumentAdminOut])
def list_user_documents(user_id: int, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                        db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return svc.list_all_documents(db, skip, limit, owner_id=user_id)


@router.get("/documents/{doc_id}/file")
def view_any_document(doc_id: int, db: Session = Depends(get_db)):
    return pdf_response(svc.get_any_document(db, doc_id))


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_any_document(doc_id: int, db: Session = Depends(get_db)):
    svc.delete_document(db, svc.get_any_document(db, doc_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
