import hashlib
import logging
from pathlib import Path
from typing import BinaryIO

import pymupdf
from sqlalchemy import delete, func, select
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

        # 3. Validate PDF format and inspect page count
        if not file_bytes.startswith(b"%PDF"):
            raise DocumentServiceError("Invalid file format. Only PDF files are supported.")

        try:
            pdf_doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            incoming_page_count = len(pdf_doc)
            pdf_doc.close()
        except Exception as e:
            raise DocumentServiceError(f"Corrupted or unreadable PDF document: {e}")

        if incoming_page_count == 0:
            raise DocumentServiceError("The uploaded PDF document contains 0 pages.")

        # 4. Enforce Single Document Pilot Limit
        if incoming_page_count > self.settings.max_pages_per_doc:
            raise DocumentServiceError(
                f"Pilot quota exceeded: A single document cannot exceed {self.settings.max_pages_per_doc} pages. "
                f"Uploaded document '{filename}' has {incoming_page_count} pages."
            )

        # 5. Calculate Current Project Page Usage
        current_project_pages = db.scalar(
            select(func.coalesce(func.sum(Document.page_count), 0)).where(
                Document.project_id == project_id,
                Document.status.in_(("ready", "processing", "pending")),
            )
        ) or 0

        # 6. SHA-256 Deduplication check
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
                # Retrying failed upload
                if current_project_pages + incoming_page_count > self.settings.max_pages_per_project:
                    raise DocumentServiceError(
                        f"Pilot project quota exceeded: This project currently has {current_project_pages}/{self.settings.max_pages_per_project} pages. "
                        f"Adding '{filename}' ({incoming_page_count} pages) would exceed the maximum pilot limit of {self.settings.max_pages_per_project} pages."
                    )
                existing.status = "pending"
                existing.page_count = incoming_page_count
                existing.error_message = None
                db.commit()
                db.refresh(existing)
                # Ensure file is written to disk
                file_path = self._get_file_path(existing.id)
                file_path.write_bytes(file_bytes)
                return existing, False

        # Enforce Cumulative Project Pilot Limit
        if current_project_pages + incoming_page_count > self.settings.max_pages_per_project:
            raise DocumentServiceError(
                f"Pilot project quota exceeded: This project currently has {current_project_pages}/{self.settings.max_pages_per_project} pages. "
                f"Adding '{filename}' ({incoming_page_count} pages) would exceed the maximum pilot limit of {self.settings.max_pages_per_project} pages."
            )

        # 7. Create new Document record with page count
        doc = Document(
            project_id=project_id,
            filename=filename,
            file_hash=file_hash,
            file_size_bytes=len(file_bytes),
            status="pending",
            page_count=incoming_page_count,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Save to local storage
        file_path = self._get_file_path(doc.id)
        file_path.write_bytes(file_bytes)

        return doc, False

    def get_project_quota_stats(self, project_id: str, db: Session) -> dict:
        """Compute current pilot quota statistics for a research project."""
        total_pages = db.scalar(
            select(func.coalesce(func.sum(Document.page_count), 0)).where(
                Document.project_id == project_id,
                Document.status.in_(("ready", "processing", "pending")),
            )
        ) or 0
        max_limit = self.settings.max_pages_per_project
        return {
            "total_pages": int(total_pages),
            "max_pages_limit": int(max_limit),
            "remaining_pages": max(0, int(max_limit - total_pages)),
        }

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
