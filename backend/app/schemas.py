from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    question: str = Field(min_length=12, max_length=2000)
    title: str | None = Field(default=None, max_length=240)


class ProjectCreated(BaseModel):
    project_id: str
    run_id: str
    status: str


class RunEventOut(BaseModel):
    stage: str
    status: str
    message: str
    metadata: dict = Field(default_factory=dict)
    occurred_at: datetime


class RunOut(BaseModel):
    id: str
    project_id: str
    status: str
    provider_name: str
    model_name: str
    started_at: datetime | None
    completed_at: datetime | None
    error_summary: str | None
    source_count: int
    claim_count: int
    conclusion_count: int


class ProjectOut(BaseModel):
    id: str
    title: str
    original_question: str
    created_at: datetime
    latest_run: RunOut | None


class SourceOut(BaseModel):
    id: str
    title: str | None
    canonical_url: str
    publisher: str | None
    source_type: str
    retrieved_at: datetime | None
    fetch_status: str | None


class ClaimOut(BaseModel):
    id: str
    topic: str
    statement: str
    classification: str
    confidence: str
    exact_excerpt: str
    source: SourceOut


class AssessmentOut(BaseModel):
    id: str
    left_claim_id: str
    right_claim_id: str
    relationship: Literal["supports", "qualifies", "contradicts", "unrelated"]
    rationale: str
    conditions: str
    confidence: str


class ConclusionOut(BaseModel):
    id: str
    statement: str
    confidence: str
    limitations: str
    claim_count: int


class RunDetail(RunOut):
    question: str
    plan_items: list[str]
    conclusions: list[ConclusionOut]


class TraceOut(BaseModel):
    conclusion: ConclusionOut
    claims: list[ClaimOut]
    assessments: list[AssessmentOut]
