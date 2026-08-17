import json
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .auth import (
    AuthenticatedUser,
    QuotaService,
    auth_router,
    get_current_user,
    get_optional_user,
    require_user_quota,
)

logger = logging.getLogger(__name__)
quota_service = QuotaService()
from .config import get_settings
from .database import Base, engine, get_db, init_db
from .documents.router import router as documents_router
from .rag.reranker import get_reranker
from .rag.router import router as rag_router
from .models import (
    Claim,
    Conclusion,
    ConclusionClaim,
    Document,
    EvidenceAssessment,
    PlanItem,
    RAGReport,
    ResearchProject,
    ResearchRun,
    RunEvent,
    Source,
    SourceSnapshot,
    utc_now,
)
from .rate_limiter import rate_limit
from .schemas import (
    ActiveRAGVault,
    ActiveWebProject,
    AssessmentOut,
    ClaimOut,
    ConclusionOut,
    ProjectCreate,
    ProjectCreated,
    ProjectOut,
    RAGVaultCreate,
    RAGVaultOut,
    RunDetail,
    RunEventOut,
    RunOut,
    SourceOut,
    TraceOut,
    WorkspaceBootstrapOut,
)
from .services import create_project_and_run, create_retry_run, get_bulk_run_counts, get_run_counts, run_research


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_reranker()  # Warm up FlashRank cross-encoder model
    yield


settings = get_settings()
app = FastAPI(title="Enterprise Research Agent API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "X-Content-Type-Options"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")


def source_out(db: Session, snapshot: SourceSnapshot) -> SourceOut:
    source = db.get(Source, snapshot.source_id) if snapshot else None
    return SourceOut(
        id=source.id if source else (snapshot.source_id if snapshot else ""),
        title=(source.title if source else "") or "Untitled Source",
        canonical_url=(source.canonical_url if source else "") or "",
        publisher=(source.publisher if source else "") or "",
        source_type=(source.source_type if source else "web"),
        retrieved_at=snapshot.retrieved_at if snapshot else utc_now(),
        fetch_status=snapshot.fetch_status if snapshot else "failed",
    )


def claim_out(db: Session, claim: Claim) -> ClaimOut:
    snapshot = db.get(SourceSnapshot, claim.snapshot_id) if claim else None
    return ClaimOut(
        id=claim.id if claim else "",
        topic=claim.topic if claim else "",
        statement=claim.statement if claim else "",
        classification=claim.classification if claim else "impact",
        confidence=claim.confidence if claim else "medium",
        exact_excerpt=claim.exact_excerpt if claim else "",
        source=source_out(db, snapshot),
    )


def assessment_out(assessment: EvidenceAssessment) -> AssessmentOut:
    return AssessmentOut(
        id=assessment.id,
        left_claim_id=assessment.left_claim_id,
        right_claim_id=assessment.right_claim_id,
        relationship=assessment.relationship,
        rationale=assessment.rationale,
        conditions=assessment.conditions,
        confidence=assessment.confidence,
    )


def conclusion_out(db: Session, conclusion: Conclusion) -> ConclusionOut:
    count = db.query(ConclusionClaim).filter(ConclusionClaim.conclusion_id == conclusion.id).count()
    return ConclusionOut(
        id=conclusion.id,
        statement=conclusion.statement,
        confidence=conclusion.confidence,
        reasoning=getattr(conclusion, "reasoning", "") or "",
        limitations=conclusion.limitations or "",
        claim_count=count,
    )


def run_out(db: Session, run: ResearchRun) -> RunOut:
    source_count, claim_count, conclusion_count = get_run_counts(db, run.id)
    return RunOut(
        id=run.id,
        project_id=run.project_id,
        status=run.status,
        provider_name=run.provider_name,
        model_name=run.model_name,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_summary=run.error_summary,
        source_count=source_count,
        claim_count=claim_count,
        conclusion_count=conclusion_count,
    )


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "ai_provider": settings.effective_provider,
        "model": settings.effective_model_name,
        "providers_configured": {
            "ai": settings.is_ai_configured,
            "bedrock": bool(settings.effective_provider == "bedrock" and (settings.effective_bedrock_bearer_token or settings.aws_access_key_id)),
            "openai_compatible": bool(settings.effective_provider == "openai_compatible" and settings.effective_api_key),
            "tavily": bool(settings.tavily_api_key),
        },
    }


@app.post(
    "/api/v1/research-projects",
    response_model=ProjectCreated,
    status_code=202,
    dependencies=[Depends(rate_limit(settings.rate_limit_research_per_min, 60))],
)
def create_research_project(
    payload: ProjectCreate,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(require_user_quota),
    db: Session = Depends(get_db),
):
    """Create a new research project and run, bounded by user quota and stamped with user_id."""
    project, run = create_project_and_run(
        db,
        payload.question.strip(),
        payload.title.strip() if payload.title else None,
        user_id=user.id,
    )
    background_tasks.add_task(run_research, run.id)
    return ProjectCreated(project_id=project.id, run_id=run.id, status=run.status)


def bulk_project_outs(db: Session, projects: list[ResearchProject]) -> list[ProjectOut]:
    """Batch builds ProjectOut objects with their latest run and aggregated counts in O(1) DB roundtrips."""
    if not projects:
        return []
    project_ids = [p.id for p in projects]

    # 1. Fetch latest run for each project in 1 window-partition query
    ranked_runs_stmt = (
        select(
            ResearchRun,
            func.row_number().over(
                partition_by=ResearchRun.project_id,
                order_by=(desc(ResearchRun.created_at), desc(ResearchRun.id)),
            ).label("rn"),
        )
        .where(ResearchRun.project_id.in_(project_ids))
        .subquery()
    )
    latest_runs_stmt = (
        select(ResearchRun)
        .join(ranked_runs_stmt, ResearchRun.id == ranked_runs_stmt.c.id)
        .where(ranked_runs_stmt.c.rn == 1)
    )
    latest_runs = list(db.scalars(latest_runs_stmt).all())
    latest_run_by_proj = {r.project_id: r for r in latest_runs}

    # 2. Bulk fetch counts for all runs in 3 single aggregation passes
    run_ids = [r.id for r in latest_runs]
    counts_map = get_bulk_run_counts(db, run_ids)

    # 3. Assemble ProjectOut objects in memory
    output = []
    for p in projects:
        run = latest_run_by_proj.get(p.id)
        run_dto = None
        if run:
            sc, cc, conc = counts_map.get(run.id, (0, 0, 0))
            run_dto = RunOut(
                id=run.id,
                project_id=run.project_id,
                status=run.status,
                provider_name=run.provider_name,
                model_name=run.model_name,
                started_at=run.started_at,
                completed_at=run.completed_at,
                error_summary=run.error_summary,
                source_count=sc,
                claim_count=cc,
                conclusion_count=conc,
            )
        output.append(
            ProjectOut(
                id=p.id,
                title=p.title,
                original_question=p.original_question,
                created_at=p.created_at,
                latest_run=run_dto,
            )
        )
    return output


@app.get("/api/v1/research-projects", response_model=list[ProjectOut])
def list_projects(
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """List Web Intelligence research projects isolated strictly by authenticated user."""
    if not user:
        return []

    query = (
        select(ResearchProject)
        .where(ResearchProject.user_id == user.id, ResearchProject.project_type == "web")
        .order_by(desc(ResearchProject.created_at))
        .limit(50)
    )
    projects = list(db.scalars(query).all())
    return bulk_project_outs(db, projects)


@app.post(
    "/api/v1/rag-vaults",
    response_model=RAGVaultOut,
    status_code=201,
    dependencies=[Depends(rate_limit(settings.rate_limit_research_per_min, 60))],
)
def create_rag_vault(
    payload: RAGVaultCreate,
    user: AuthenticatedUser = Depends(require_user_quota),
    db: Session = Depends(get_db),
):
    """Create a pure Document RAG vault container without triggering any background web discovery."""
    project = ResearchProject(
        title=payload.title.strip(),
        original_question=payload.title.strip(),
        user_id=user.id,
        project_type="rag",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return RAGVaultOut(project_id=project.id, title=project.title, created_at=project.created_at)


@app.get("/api/v1/rag-vaults", response_model=list[RAGVaultOut])
def list_rag_vaults(
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """List Document RAG vaults isolated by authenticated user."""
    if not user:
        return []
    query = (
        select(ResearchProject)
        .where(ResearchProject.user_id == user.id, ResearchProject.project_type == "rag")
        .order_by(desc(ResearchProject.created_at))
        .limit(50)
    )
    projects = list(db.scalars(query).all())
    return [RAGVaultOut(project_id=p.id, title=p.title, created_at=p.created_at) for p in projects]


@app.get("/api/v1/research-projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Get project details with user ownership verification."""
    project = db.get(ResearchProject, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user and project.user_id and project.user_id != user.id:
        raise HTTPException(404, "Project not found")
    latest = db.scalar(
        select(ResearchRun)
        .where(ResearchRun.project_id == project.id)
        .order_by(desc(ResearchRun.created_at), desc(ResearchRun.id))
    )
    return ProjectOut(
        id=project.id,
        title=project.title,
        original_question=project.original_question,
        created_at=project.created_at,
        latest_run=run_out(db, latest) if latest else None,
    )


def verify_run_access(db: Session, run_id: str, user: AuthenticatedUser | None) -> ResearchRun:
    """Ensure run exists and belongs to the authenticated user (anti-IDOR/BOLA)."""
    run = db.get(ResearchRun, run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    if user:
        project = db.get(ResearchProject, run.project_id)
        if project and project.user_id and project.user_id != user.id:
            raise HTTPException(404, "Research run not found")
    return run


def verify_conclusion_access(db: Session, conclusion_id: str, user: AuthenticatedUser | None) -> Conclusion:
    """Ensure conclusion exists and belongs to the authenticated user (anti-IDOR/BOLA)."""
    conclusion = db.get(Conclusion, conclusion_id)
    if not conclusion:
        raise HTTPException(404, "Conclusion not found")
    if user:
        run = db.get(ResearchRun, conclusion.run_id)
        if run:
            project = db.get(ResearchProject, run.project_id)
            if project and project.user_id and project.user_id != user.id:
                raise HTTPException(404, "Conclusion not found")
    return conclusion


@app.get("/api/v1/research-projects/{project_id}/runs", response_model=list[RunOut])
def list_project_runs(
    project_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    project = db.get(ResearchProject, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user and project.user_id and project.user_id != user.id:
        raise HTTPException(404, "Project not found")
    runs = list(
        db.scalars(
            select(ResearchRun)
            .where(ResearchRun.project_id == project_id)
            .order_by(desc(ResearchRun.created_at), desc(ResearchRun.id))
        ).all()
    )
    return [run_out(db, run) for run in runs]


@app.get("/api/v1/research-runs/{run_id}", response_model=RunDetail)
def get_run(
    run_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    run = verify_run_access(db, run_id, user)
    project = db.get(ResearchProject, run.project_id)
    base = run_out(db, run).model_dump()
    plan_items = list(db.scalars(select(PlanItem).where(PlanItem.run_id == run_id).order_by(PlanItem.item_type, PlanItem.position)).all())
    conclusions = list(db.scalars(select(Conclusion).where(Conclusion.run_id == run_id)).all())
    question = project.original_question if project else ""
    return RunDetail(**base, question=question, plan_items=[item.text for item in plan_items], conclusions=[conclusion_out(db, item) for item in conclusions])


@app.get("/api/v1/research-runs/{run_id}/events", response_model=list[RunEventOut])
def get_events(
    run_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    verify_run_access(db, run_id, user)
    events = list(db.scalars(select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.occurred_at, RunEvent.id)).all())
    return [RunEventOut(stage=item.stage, status=item.status, message=item.message, metadata=json.loads(item.metadata_json or "{}"), occurred_at=item.occurred_at) for item in events]


@app.get("/api/v1/research-runs/{run_id}/sources", response_model=list[SourceOut])
def get_sources(
    run_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    verify_run_access(db, run_id, user)
    snapshots = list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == run_id).order_by(SourceSnapshot.retrieved_at)).all())
    return [source_out(db, item) for item in snapshots]


@app.get("/api/v1/research-runs/{run_id}/claims", response_model=list[ClaimOut])
def get_claims(
    run_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    verify_run_access(db, run_id, user)
    claims = list(db.scalars(select(Claim).where(Claim.run_id == run_id).order_by(Claim.topic)).all())
    return [claim_out(db, item) for item in claims]


@app.get("/api/v1/research-runs/{run_id}/assessments", response_model=list[AssessmentOut])
def get_assessments(
    run_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    verify_run_access(db, run_id, user)
    assessments = list(
        db.scalars(
            select(EvidenceAssessment)
            .distinct()
            .join(Claim, EvidenceAssessment.left_claim_id == Claim.id)
            .where(Claim.run_id == run_id)
        ).all()
    )
    return [assessment_out(item) for item in assessments]


@app.get("/api/v1/conclusions/{conclusion_id}/trace", response_model=TraceOut)
def get_conclusion_trace(
    conclusion_id: str,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    conclusion = verify_conclusion_access(db, conclusion_id, user)
    links = list(db.scalars(select(ConclusionClaim).where(ConclusionClaim.conclusion_id == conclusion.id)).all())
    if not links:
        raise HTTPException(409, "Conclusion has no linked evidence and cannot be traced")
    claims = [db.get(Claim, link.claim_id) for link in links]
    claim_ids = {claim.id for claim in claims if claim}
    assessments = list(
        db.scalars(
            select(EvidenceAssessment).where(
                EvidenceAssessment.left_claim_id.in_(claim_ids) | EvidenceAssessment.right_claim_id.in_(claim_ids)
            )
        ).all()
    ) if claim_ids else []
    return TraceOut(conclusion=conclusion_out(db, conclusion), claims=[claim_out(db, claim) for claim in claims if claim], assessments=[assessment_out(item) for item in assessments])


@app.post(
    "/api/v1/research-runs/{run_id}/retry",
    response_model=RunOut,
    status_code=202,
    dependencies=[Depends(rate_limit(settings.rate_limit_research_per_min, 60))],
)
def retry_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    user: AuthenticatedUser = Depends(require_user_quota),
    db: Session = Depends(get_db),
):
    """Retry a failed research run, bounded by user quota and project ownership."""
    run = db.get(ResearchRun, run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    project = db.get(ResearchProject, run.project_id)
    if project and project.user_id and project.user_id != user.id:
        raise HTTPException(404, "Research run not found")
    if run.status not in {"failed", "partial"}:
        raise HTTPException(409, "Only failed or partial runs can be retried")
    retry = create_retry_run(db, run)
    background_tasks.add_task(run_research, retry.id)
    return run_out(db, retry)


@app.get("/api/v1/workspace/bootstrap", response_model=WorkspaceBootstrapOut)
def get_workspace_bootstrap(
    response: Response,
    user: AuthenticatedUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Fast consolidated workspace bootstrap endpoint returning user, quota, web, and RAG session state in 1 call."""
    # Security headers prevent proxy caching and cross-user leaks
    response.headers["Cache-Control"] = "private, no-cache, no-transform"
    response.headers["Vary"] = "Authorization"
    response.headers["X-Content-Type-Options"] = "nosniff"

    if not user:
        return WorkspaceBootstrapOut()

    # 1. Fetch quota
    quota_dict = None
    try:
        quota = quota_service.get_or_create_quota(user.id, db)
        remaining = max(0, quota.max_free_runs - quota.total_runs_used)
        quota_dict = {
            "user_id": quota.user_id,
            "total_runs_used": quota.total_runs_used,
            "max_free_runs": quota.max_free_runs,
            "remaining_runs": remaining,
            "is_quota_exhausted": quota.total_runs_used >= quota.max_free_runs,
        }
    except Exception as exc:
        logger.warning("Failed to fetch quota during bootstrap: %s", exc)

    user_dict = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }

    # 2. Fetch Web Projects (Batched O(1) queries with bulk_project_outs)
    web_projects_rows = list(
        db.scalars(
            select(ResearchProject)
            .where(ResearchProject.user_id == user.id, ResearchProject.project_type == "web")
            .order_by(desc(ResearchProject.created_at))
            .limit(50)
        ).all()
    )
    web_projects_out = bulk_project_outs(db, web_projects_rows)

    # 3. Active Web Project details (if any)
    active_web = None
    if web_projects_rows:
        latest_web = web_projects_rows[0]
        latest_run = db.scalar(
            select(ResearchRun)
            .where(ResearchRun.project_id == latest_web.id)
            .order_by(desc(ResearchRun.created_at))
        )
        if latest_run:
            sources = [
                source_out(db, item)
                for item in db.scalars(
                    select(SourceSnapshot)
                    .where(SourceSnapshot.run_id == latest_run.id)
                    .order_by(SourceSnapshot.retrieved_at)
                ).all()
            ]
            claims = [claim_out(db, item) for item in db.scalars(select(Claim).where(Claim.run_id == latest_run.id)).all()]
            events = [
                RunEventOut(
                    stage=item.stage,
                    status=item.status,
                    message=item.message,
                    metadata=json.loads(item.metadata_json or "{}"),
                    occurred_at=item.occurred_at,
                )
                for item in db.scalars(select(RunEvent).where(RunEvent.run_id == latest_run.id).order_by(RunEvent.occurred_at, RunEvent.id)).all()
            ]
            assessments = [
                assessment_out(item)
                for item in db.scalars(
                    select(EvidenceAssessment)
                    .distinct()
                    .join(Claim, EvidenceAssessment.left_claim_id == Claim.id)
                    .where(Claim.run_id == latest_run.id)
                ).all()
            ]
            base = run_out(db, latest_run).model_dump()
            plan_items = list(db.scalars(select(PlanItem).where(PlanItem.run_id == latest_run.id).order_by(PlanItem.item_type, PlanItem.position)).all())
            conclusions = list(db.scalars(select(Conclusion).where(Conclusion.run_id == latest_run.id)).all())
            run_detail = RunDetail(**base, question=latest_web.original_question, plan_items=[item.text for item in plan_items], conclusions=[conclusion_out(db, item) for item in conclusions])
            active_web = ActiveWebProject(
                project=web_projects_out[0],
                run=run_detail,
                sources=sources,
                claims=claims,
                events=events,
                assessments=assessments,
            )

    # 4. Fetch RAG Vaults
    rag_vault_rows = list(
        db.scalars(
            select(ResearchProject)
            .where(ResearchProject.user_id == user.id, ResearchProject.project_type == "rag")
            .order_by(desc(ResearchProject.created_at))
            .limit(50)
        ).all()
    )
    rag_vaults_out = [
        RAGVaultOut(project_id=v.id, title=v.title, created_at=v.created_at)
        for v in rag_vault_rows
    ]

    # 5. Active RAG Vault details (if any)
    active_rag = None
    if rag_vault_rows:
        latest_vault = rag_vault_rows[0]
        docs = list(
            db.scalars(
                select(Document)
                .where(Document.project_id == latest_vault.id)
                .order_by(desc(Document.created_at))
            ).all()
        )
        reports = list(
            db.scalars(
                select(RAGReport)
                .where(RAGReport.project_id == latest_vault.id)
                .order_by(desc(RAGReport.created_at))
            ).all()
        )
        total_pages = sum(d.page_count or 0 for d in docs)
        max_limit = 10
        docs_json = [
            {
                "id": d.id,
                "project_id": d.project_id,
                "filename": d.filename,
                "file_hash": d.file_hash,
                "file_size_bytes": d.file_size_bytes,
                "status": d.status,
                "page_count": d.page_count,
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "completed_at": d.completed_at.isoformat() if d.completed_at else None,
            }
            for d in docs
        ]
        reports_json = []
        for r in reports:
            try:
                data = json.loads(r.report_json) if r.report_json else {}
            except Exception:
                data = {}
            reports_json.append(
                {
                    "id": r.id,
                    "project_id": r.project_id,
                    "question": r.question,
                    "summary": data.get("summary", ""),
                    "sections": data.get("sections", []),
                    "limitations": data.get("limitations", ""),
                    "total_sources_cited": data.get("total_sources_cited", 0),
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        active_rag = ActiveRAGVault(
            vault=RAGVaultOut(project_id=latest_vault.id, title=latest_vault.title, created_at=latest_vault.created_at),
            documents=docs_json,
            reports=reports_json,
            total_pages=total_pages,
            max_pages_limit=max_limit,
            remaining_pages=max(0, max_limit - total_pages),
        )

    return WorkspaceBootstrapOut(
        user=user_dict,
        quota=quota_dict,
        web_projects=web_projects_out,
        active_web=active_web,
        rag_vaults=rag_vaults_out,
        active_rag=active_rag,
    )

