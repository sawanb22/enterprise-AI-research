import uuid
from datetime import datetime, timezone

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
    title: Mapped[str] = mapped_column(String(240))
    original_question: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    provider_name: Mapped[str] = mapped_column(String(80), default="groq")
    model_name: Mapped[str] = mapped_column(String(160))
    limits_json: Mapped[str] = mapped_column(Text, default="{}")
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
    limitations: Mapped[str] = mapped_column(Text, default="")


class ConclusionClaim(Base):
    __tablename__ = "conclusion_claims"

    conclusion_id: Mapped[str] = mapped_column(ForeignKey("conclusions.id", ondelete="CASCADE"), primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(24), default="supports")
