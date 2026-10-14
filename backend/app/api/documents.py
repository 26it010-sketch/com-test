from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import get_current_user
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut
from app.services import document_service as svc

router = APIRouter(prefix="/documents", tags=["documents"])


def pdf_response(doc: Document) -> FileResponse:
    path = svc.file_path(doc)

    if not path.exists():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="File missing from storage",
        )

    print("PDF DEBUG:", path, "exists:", path.exists(), "size:", path.stat().st_size)

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=doc.original_filename,
        content_disposition_type="inline",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    return await svc.save_pdf(db, user, file)


@router.get("", response_model=list[DocumentOut])
def list_my_documents(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.list_user_documents(db, user, skip, limit)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_my_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.get_owned_document(db, user, doc_id)


@router.get("/{doc_id}/file")
def view_my_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return pdf_response(svc.get_owned_document(db, user, doc_id))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    svc.delete_document(db, svc.get_owned_document(db, user, doc_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
