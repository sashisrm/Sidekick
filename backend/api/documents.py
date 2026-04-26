import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from config import settings
from db.database import get_session
from db.models import Document, DocumentChunk, DocumentStatus, FileType, User, gen_uuid
from workers.tasks import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {
    "pdf": FileType.pdf,
    "docx": FileType.docx,
    "xlsx": FileType.xlsx,
    "pptx": FileType.pptx,
    "md": FileType.md,
    "txt": FileType.txt,
}


class DocumentOut(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    page_count: int | None
    chunk_count: int
    uploaded_at: str
    ingested_at: str | None

    class Config:
        from_attributes = True


class DocumentStatusOut(BaseModel):
    id: str
    status: str
    chunk_count: int
    error_message: str | None


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not supported")

    doc_id = gen_uuid()
    safe_filename = f"{doc_id}.{ext}"
    upload_path = Path(settings.upload_dir) / safe_filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = upload_path.stat().st_size

    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename,
        file_type=ALLOWED_EXTENSIONS[ext],
        file_size_bytes=file_size,
        file_path=str(upload_path),
        status=DocumentStatus.pending,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    # Enqueue background ingestion job
    await ingest_document_task(doc_id)

    return _doc_out(doc)


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.uploaded_at.desc())
    )
    docs = result.scalars().all()
    return [_doc_out(d) for d in docs]


@router.get("/{doc_id}/status", response_model=DocumentStatusOut)
async def document_status(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    doc = await _get_doc(doc_id, current_user.id, session)
    return DocumentStatusOut(
        id=doc.id,
        status=doc.status.value,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    doc = await _get_doc(doc_id, current_user.id, session)

    # Remove vectors from ChromaDB
    try:
        from pipelines.ingestion.indexer import delete_document_vectors
        await delete_document_vectors(doc_id)
    except Exception:
        pass  # Don't fail deletion if ChromaDB cleanup fails

    # Remove file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await session.delete(doc)
    await session.commit()


# --- Helpers ---

async def _get_doc(doc_id: str, user_id: str, session: AsyncSession) -> Document:
    result = await session.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def _doc_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type.value,
        file_size_bytes=doc.file_size_bytes,
        status=doc.status.value,
        error_message=doc.error_message,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        uploaded_at=doc.uploaded_at.isoformat(),
        ingested_at=doc.ingested_at.isoformat() if doc.ingested_at else None,
    )
