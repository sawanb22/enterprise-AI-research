from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RAGResearchRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Research question to analyze against project documents")


class PageCitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    document_filename: str
    page_number: int
    chunk_index: int
    verbatim_quote: str
    score: float | None = None


class ReportSection(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    heading: str
    content: str
    confidence: Literal["low", "medium", "high"] = "high"
    citations: list[PageCitation] = Field(default_factory=list)


class RAGReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    question: str
    summary: str
    sections: list[ReportSection]
    limitations: str = ""
    total_sources_cited: int = 0
    status: str = "completed"
    created_at: datetime


class RAGReportListOut(BaseModel):
    reports: list[RAGReportOut]
    total: int


class ScoredChunk(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    document_id: str
    document_filename: str
    page_number: int
    chunk_index: int
    raw_text: str
    visual_summary: str = ""
    combined_context: str
    token_count: int = 0
    score: float = 0.0
