import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.factory import get_llm_provider
from ..config import Settings, get_settings
from ..database import get_db
from ..models import RAGReport, ResearchProject
from .reranker import get_reranker
from .retrieval import VectorRetriever
from .schemas import PageCitation, RAGReportListOut, RAGReportOut, RAGResearchRequest, ReportSection
from .synthesis import RAGSynthesizer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rag-research"])


def _parse_report_out(report: RAGReport) -> RAGReportOut:
    """Helper to deserialize a RAGReport ORM model into RAGReportOut schema."""
    try:
        data = json.loads(report.report_json)
    except Exception:
        data = {}

    raw_sections = data.get("sections", [])
    sections = []
    for s in raw_sections:
        cits = [PageCitation(**c) for c in s.get("citations", [])]
        sections.append(
            ReportSection(
                heading=s.get("heading", ""),
                content=s.get("content", ""),
                confidence=s.get("confidence", "high"),
                citations=cits,
            )
        )

    return RAGReportOut(
        id=report.id,
        project_id=report.project_id,
        question=report.question,
        summary=data.get("summary", ""),
        sections=sections,
        limitations=data.get("limitations", ""),
        total_sources_cited=data.get("total_sources_cited", 0),
        status=report.status,
        created_at=report.created_at,
    )


@router.post(
    "/projects/{project_id}/rag-research",
    response_model=RAGReportOut,
    status_code=status.HTTP_200_OK,
)
def execute_rag_research(
    project_id: str,
    req: RAGResearchRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """
    Execute end-to-end Enterprise RAG research on project documents:
    Multi-query expansion -> pgvector retrieval -> FlashRank cross-encoder rerank -> Grounded synthesis with citation gate.
    """
    # 1. Verify project exists
    project = db.scalar(select(ResearchProject).where(ResearchProject.id == project_id))
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found",
        )

    try:
        # 2. Initialize components
        llm = get_llm_provider(settings)
        retriever = VectorRetriever(settings)
        reranker = get_reranker()
        synthesizer = RAGSynthesizer(llm)

        # 3. Retrieve candidates (top 50)
        candidates = retriever.retrieve_candidates(
            project_id=project_id,
            query=req.question,
            db=db,
            top_k=settings.max_rerank_candidates,
            llm=llm,
        )

        # 4. Rerank candidates (top 15)
        ranked_chunks = reranker.rerank(
            query=req.question,
            candidates=candidates,
            top_k=settings.max_rag_results,
        )

        # 5. Synthesize report & verify citations
        report = synthesizer.synthesize(
            question=req.question,
            ranked_chunks=ranked_chunks,
            project_id=project_id,
            db=db,
        )

        return report

    except Exception as exc:
        logger.exception("RAG research execution error for project '%s': %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG research failed: {exc}",
        ) from exc


@router.get(
    "/projects/{project_id}/rag-reports",
    response_model=RAGReportListOut,
)
def list_project_rag_reports(
    project_id: str,
    db: Session = Depends(get_db),
):
    """List all previously synthesized RAG reports for a project."""
    reports = list(
        db.scalars(
            select(RAGReport)
            .where(RAGReport.project_id == project_id)
            .order_by(RAGReport.created_at.desc())
        ).all()
    )
    return RAGReportListOut(
        reports=[_parse_report_out(r) for r in reports],
        total=len(reports),
    )


@router.get(
    "/rag-reports/{report_id}",
    response_model=RAGReportOut,
)
def get_rag_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve a specific RAG report by ID."""
    report = db.scalar(select(RAGReport).where(RAGReport.id == report_id))
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAG report not found",
        )
    return _parse_report_out(report)
