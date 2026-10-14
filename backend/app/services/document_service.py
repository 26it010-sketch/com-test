import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.document import Document
from app.models.user import User

CHUNK_SIZE = 1024 * 1024
PDF_MAGIC = b"%PDF-"
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def _upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_path(doc: Document) -> Path:
    """stored_filename is a server-generated UUID, so it can never contain path separators."""
    return _upload_dir() / doc.stored_filename


async def save_pdf(db: Session, owner: User, upload: UploadFile) -> Document:
    filename = os.path.basename((upload.filename or "").replace("\\", "/"))
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Only .pdf files are allowed")
    if (upload.content_type or "").lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Content type must be application/pdf")

    first = await upload.read(len(PDF_MAGIC))
    if first != PDF_MAGIC:  # content sniffing: extension and header can both be spoofed
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="File is not a valid PDF")

    stored_name = f"{uuid.uuid4().hex}.pdf"
    dest = _upload_dir() / stored_name
    size = len(first)
    try:
        with open(dest, "wb") as out:
            out.write(first)
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > settings.max_upload_bytes:  # enforced while streaming, not after
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
                    )
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    doc = Document(owner_id=owner.id, original_filename=filename[:255],
                   stored_filename=stored_name, size_bytes=size)
    db.add(doc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        dest.unlink(missing_ok=True)
        raise
    db.refresh(doc)
    return doc


def list_user_documents(db: Session, user: User, skip: int, limit: int) -> list[Document]:
    stmt = (select(Document).where(Document.owner_id == user.id)
            .order_by(Document.uploaded_at.desc(), Document.id.desc()).offset(skip).limit(limit))
    return list(db.scalars(stmt))


def list_all_documents(db: Session, skip: int, limit: int, owner_id: int | None = None) -> list[Document]:
    stmt = (select(Document).options(joinedload(Document.owner))
            .order_by(Document.uploaded_at.desc(), Document.id.desc()))
    if owner_id is not None:
        stmt = stmt.where(Document.owner_id == owner_id)
    return list(db.scalars(stmt.offset(skip).limit(limit)))


def get_owned_document(db: Session, user: User, doc_id: int) -> Document:
    """Returns 404 (not 403) for other people's documents so IDs can't be probed."""
    doc = db.get(Document, doc_id)
    if doc is None or doc.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def get_any_document(db: Session, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def delete_document(db: Session, doc: Document) -> None:
    path = file_path(doc)
    db.delete(doc)
    db.commit()
    path.unlink(missing_ok=True)  # remove the file only after the DB row is gone
