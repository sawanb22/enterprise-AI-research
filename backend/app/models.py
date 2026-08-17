import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    project_type: Mapped[str] = mapped_column(String(32), default="web", index=True)
    title: Mapped[str] = mapped_column(String(240))
    original_question: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    provider_name: Mapped[str] = mapped_column(String(80), default="bedrock")
    model_name: Mapped[str] = mapped_column(String(160))
    limits_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlanItem(Base):
    __tablename__ = "plan_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    canonical_url: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(240), nullable=True)
    author: Mapped[str | None] = mapped_column(String(240), nullable=True)
    published_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), default="public_web")
    first_retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (UniqueConstraint("run_id", "source_id", "content_hash", name="uq_run_source_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    content_hash: Mapped[str] = mapped_column(String(64))
    cleaned_text: Mapped[str] = mapped_column(Text)
    fetch_status: Mapped[str] = mapped_column(String(32), default="fetched")
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("source_snapshots.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(String(160))
    statement: Mapped[str] = mapped_column(Text)
    classification: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[str] = mapped_column(String(16))
    exact_excerpt: Mapped[str] = mapped_column(Text)
    excerpt_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt_end: Mapped[int | None] = mapped_column(Integer, nullable=True)


class EvidenceAssessment(Base):
    __tablename__ = "evidence_assessments"
    __table_args__ = (UniqueConstraint("left_claim_id", "right_claim_id", name="uq_claim_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    left_claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    right_claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    relationship: Mapped[str] = mapped_column(String(24))
    rationale: Mapped[str] = mapped_column(Text)
    conditions: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String(16))


class Conclusion(Base):
    __tablename__ = "conclusions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    statement: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(16))
    reasoning: Mapped[str] = mapped_column(Text, default="")
    limitations: Mapped[str] = mapped_column(Text, default="")


class ConclusionClaim(Base):
    __tablename__ = "conclusion_claims"

    conclusion_id: Mapped[str] = mapped_column(ForeignKey("conclusions.id", ondelete="CASCADE"), primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(24), default="supports")


# ============================================================================
# Enterprise Document RAG Models
# ============================================================================

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("project_id", "file_hash", name="uq_project_file"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    raw_text: Mapped[str] = mapped_column(Text)
    visual_summary: Mapped[str] = mapped_column(Text, default="")
    combined_context: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding = mapped_column(Vector(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RAGReport(Base):
    __tablename__ = "rag_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text)
    report_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default="generating")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RAGReportCitation(Base):
    __tablename__ = "rag_report_citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    report_id: Mapped[str] = mapped_column(ForeignKey("rag_reports.id", ondelete="CASCADE"), index=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True)
    section_index: Mapped[int] = mapped_column(Integer, default=0)
    verbatim_quote: Mapped[str] = mapped_column(Text)
