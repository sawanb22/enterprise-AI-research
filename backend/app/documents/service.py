import hashlib
import logging
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..embeddings.provider import EmbeddingProvider
from ..models import Document, DocumentChunk, ResearchProject, utc_now
from .chunker import SmartChunker
from .parser import PDFParser
from .vision import VisionProcessor

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    pass


class DocumentService:
    """Core service for managing document uploads, parsing, embedding, and storage."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.parser = PDFParser()
        self.chunker = SmartChunker(
            target_tokens=self.settings.chunk_target_tokens,
            overlap_tokens=self.settings.chunk_overlap_tokens,
        )
        self.embedder = EmbeddingProvider(self.settings)
        self.vision = VisionProcessor(self.settings)

        # Uploads storage directory
        self.upload_dir = Path("./data/uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_file_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(file_bytes).hexdigest()

    def _get_file_path(self, document_id: str) -> Path:
        return self.upload_dir / f"{document_id}.pdf"

    def upload_document(
        self,
        project_id: str,
        filename: str,
        file_bytes: bytes,
        db: Session,
    ) -> tuple[Document, bool]:
        """
        Validate, deduplicate, and register a new PDF document.
        Returns tuple: (Document, is_existing)
        """
        # 1. Verify project exists
        project = db.scalar(select(ResearchProject).where(ResearchProject.id == project_id))
        if not project:
            raise DocumentServiceError(f"Project '{project_id}' does not exist")

        # 2. Validate file size
        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise DocumentServiceError(
                f"File exceeds maximum allowed size of {self.settings.max_upload_size_mb} MB"
            )

        # 3. Validate PDF header
        if not file_bytes.startswith(b"%PDF"):
            raise DocumentServiceError("Invalid file format. Only PDF files are supported.")

        # 4. SHA-256 Deduplication check
        file_hash = self.compute_file_hash(file_bytes)
        existing = db.scalar(
            select(Document).where(
                Document.project_id == project_id,
                Document.file_hash == file_hash,
            )
        )

        if existing:
            # If already processed or processing, return existing record
            if existing.status in ("ready", "processing", "pending"):
                return existing, True
            else:
                # Retry failed upload
                existing.status = "pending"
                existing.error_message = None
                db.commit()
                db.refresh(existing)
                # Ensure file is written to disk
                file_path = self._get_file_path(existing.id)
                file_path.write_bytes(file_bytes)
                return existing, False

        # 5. Create new Document record
        doc = Document(
            project_id=project_id,
            filename=filename,
            file_hash=file_hash,
            file_size_bytes=len(file_bytes),
            status="pending",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Save to local storage
        file_path = self._get_file_path(doc.id)
        file_path.write_bytes(file_bytes)

        return doc, False

    def process_document(self, document_id: str, db: Session) -> Document:
        """
        Execute full document ingestion:
        Parse PDF -> Extract Tables & Diagrams -> Chunk -> Batch Embed -> Store Chunks.
        """
        doc = db.scalar(select(Document).where(Document.id == document_id))
        if not doc:
            raise DocumentServiceError(f"Document '{document_id}' not found")

        doc.status = "processing"
        doc.error_message = None
        db.commit()

        file_path = self._get_file_path(doc.id)
        if not file_path.exists():
            doc.status = "failed"
            doc.error_message = f"Uploaded file {file_path} not found on disk"
            db.commit()
            return doc

        try:
            # 1. Parse PDF pages
            pages = self.parser.parse_file(str(file_path))
            doc.page_count = len(pages)

            # 2. Process visual diagrams (with limit cap)
            visual_summaries: dict[int, str] = {}
            vision_calls = 0

            for page in pages:
                if page.images and vision_calls < self.settings.max_vision_calls_per_doc:
                    # Summarize top visual on the page
                    summary = self.vision.summarize_image(
                        page.images[0],
                        page_context=page.text[:300],
                    )
                    if summary:
                        visual_summaries[page.page_number] = summary
                        vision_calls += 1

            # 3. Chunk pages
            chunks = self.chunker.chunk_pages(pages, visual_summaries=visual_summaries)

            # 4. Generate embeddings in batch
            contexts_to_embed = [chunk.combined_context for chunk in chunks]
            embeddings = self.embedder.embed(contexts_to_embed, input_type="search_document")

            # 5. Clear any old chunks (in case of re-processing) and bulk insert new chunks
            db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
            
            chunk_records = []
            for chunk_data, emb in zip(chunks, embeddings):
                record = DocumentChunk(
                    document_id=doc.id,
                    page_number=chunk_data.page_number,
                    chunk_index=chunk_data.chunk_index,
                    raw_text=chunk_data.raw_text,
                    visual_summary=chunk_data.visual_summary,
                    combined_context=chunk_data.combined_context,
                    token_count=chunk_data.token_count,
                    embedding=emb,
                )
                chunk_records.append(record)

            db.add_all(chunk_records)
            
            # 6. Mark document ready
            doc.status = "ready"
            doc.completed_at = utc_now()
            db.commit()
            db.refresh(doc)
            return doc

        except Exception as exc:
            logger.exception("Document processing failed for '%s': %s", doc.id, exc)
            doc.status = "failed"
            doc.error_message = str(exc)
            db.commit()
            db.refresh(doc)
            return doc

    def get_document(self, document_id: str, db: Session) -> Document | None:
        """Get document by ID."""
        return db.scalar(select(Document).where(Document.id == document_id))

    def list_project_documents(self, project_id: str, db: Session) -> list[Document]:
        """List all documents for a given project."""
        return list(
            db.scalars(
                select(Document)
                .where(Document.project_id == project_id)
                .order_by(Document.created_at.desc())
            )
        )

    def delete_document(self, document_id: str, db: Session) -> bool:
        """Delete document record, its chunks (via cascade), and file on disk."""
        doc = db.scalar(select(Document).where(Document.id == document_id))
        if not doc:
            return False

        db.delete(doc)
        db.commit()

        # Clean up file on disk
        file_path = self._get_file_path(document_id)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as exc:
                logger.warning("Could not delete file %s: %s", file_path, exc)

        return True
