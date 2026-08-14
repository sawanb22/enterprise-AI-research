import logging
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import Document, DocumentChunk
from .schemas import DocumentDetailOut, DocumentListOut, DocumentOut
from .service import DocumentService, DocumentServiceError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])
doc_service = DocumentService()


def process_document_background(document_id: str):
    """Background task worker function for document processing."""
    db = SessionLocal()
    try:
        doc_service.process_document(document_id, db)
    except Exception as exc:
        logger.exception("Background processing error for document '%s': %s", document_id, exc)
    finally:
        db.close()


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Upload a PDF document to a research project and trigger asynchronous background processing."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported (.pdf)",
        )

    try:
        content = await file.read()
        doc, is_existing = doc_service.upload_document(
            project_id=project_id,
            filename=file.filename,
            file_bytes=content,
            db=db,
        )

        # Enqueue background processing if document is pending
        if doc.status == "pending":
            background_tasks.add_task(process_document_background, doc.id)

        return doc

    except DocumentServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document upload endpoint error: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/projects/{project_id}/documents", response_model=DocumentListOut)
def list_documents(project_id: str, db: Session = Depends(get_db)):
    """List all documents uploaded to a research project."""
    docs = doc_service.list_project_documents(project_id, db)
    return DocumentListOut(documents=docs, total=len(docs))


@router.get("/documents/{document_id}", response_model=DocumentDetailOut)
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """Get document status, metadata, and chunk statistics."""
    doc = doc_service.get_document(document_id, db)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunk_count = db.scalar(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
    ) or 0

    return DocumentDetailOut(
        id=doc.id,
        project_id=doc.project_id,
        filename=doc.filename,
        file_hash=doc.file_hash,
        file_size_bytes=doc.file_size_bytes,
        status=doc.status,
        page_count=doc.page_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
        chunk_count=chunk_count,
    )


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document, its chunks, embeddings, and uploaded file."""
    success = doc_service.delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"deleted": True, "document_id": document_id}
