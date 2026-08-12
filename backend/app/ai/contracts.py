from dataclasses import dataclass
from typing import Any, Literal
from pydantic import BaseModel, Field


class ProviderError(RuntimeError):
    """Base exception for AI and search provider failures."""
    pass


class ProviderConfigurationError(ProviderError):
    """Raised when required credentials or settings are missing."""
    pass


@dataclass
class SearchResult:
    url: str
    title: str | None
    snippet: str
    score: float | None = None


class PlanResponse(BaseModel):
    sub_questions: list[str] = Field(min_length=1, max_length=6)
    search_queries: list[str] = Field(min_length=1, max_length=5)


class ClaimDraft(BaseModel):
    topic: str = Field(min_length=1, max_length=250)
    statement: str = Field(min_length=1, max_length=3000)
    classification: Literal["opportunity", "impact", "risk", "limitation", "trend"]
    confidence: Literal["low", "medium", "high"]
    excerpt: str = Field(min_length=5, max_length=1500)


class ClaimResponse(BaseModel):
    claims: list[ClaimDraft] = Field(max_length=15)


class AssessmentResponse(BaseModel):
    relationship: Literal["supports", "qualifies", "contradicts", "unrelated"]
    rationale: str = Field(min_length=1, max_length=3000)
    conditions: str = Field(default="", max_length=2000)
    confidence: Literal["low", "medium", "high"]


class ConclusionDraft(BaseModel):
    statement: str = Field(min_length=1, max_length=3000)
    confidence: Literal["low", "medium", "high"]
    claim_ids: list[str] = Field(min_length=1, max_length=15)
    reasoning: str = Field(default="", max_length=5000)
    limitations: str = Field(default="", max_length=3000)


class ConclusionResponse(BaseModel):
    conclusions: list[ConclusionDraft] = Field(min_length=1, max_length=8)

