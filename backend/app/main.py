import json
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .models import Claim, Conclusion, ConclusionClaim, EvidenceAssessment, PlanItem, ResearchProject, ResearchRun, RunEvent, Source, SourceSnapshot
from .schemas import AssessmentOut, ClaimOut, ConclusionOut, ProjectCreate, ProjectCreated, ProjectOut, RunDetail, RunEventOut, RunOut, SourceOut, TraceOut
from .services import create_project_and_run, create_retry_run, get_run_counts, run_research


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()
app = FastAPI(title="Enterprise Research Agent API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def source_out(db: Session, snapshot: SourceSnapshot) -> SourceOut:
    source = db.get(Source, snapshot.source_id)
    return SourceOut(
        id=source.id,
        title=source.title,
        canonical_url=source.canonical_url,
        publisher=source.publisher,
        source_type=source.source_type,
        retrieved_at=snapshot.retrieved_at,
        fetch_status=snapshot.fetch_status,
    )


def claim_out(db: Session, claim: Claim) -> ClaimOut:
    snapshot = db.get(SourceSnapshot, claim.snapshot_id)
    return ClaimOut(
        id=claim.id,
        topic=claim.topic,
        statement=claim.statement,
        classification=claim.classification,
        confidence=claim.confidence,
        exact_excerpt=claim.exact_excerpt,
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
        limitations=conclusion.limitations,
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
        "providers_configured": {"groq": bool(settings.groq_api_key), "tavily": bool(settings.tavily_api_key)},
    }


@app.post("/api/v1/research-projects", response_model=ProjectCreated, status_code=202)
def create_research_project(payload: ProjectCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project, run = create_project_and_run(db, payload.question.strip(), payload.title.strip() if payload.title else None)
    background_tasks.add_task(run_research, run.id)
    return ProjectCreated(project_id=project.id, run_id=run.id, status=run.status)


@app.get("/api/v1/research-projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = list(db.scalars(select(ResearchProject).order_by(desc(ResearchProject.created_at))).all())
    output = []
    for project in projects:
        latest = db.scalar(select(ResearchRun).where(ResearchRun.project_id == project.id).order_by(desc(ResearchRun.started_at), desc(ResearchRun.id)))
        output.append(ProjectOut(id=project.id, title=project.title, original_question=project.original_question, created_at=project.created_at, latest_run=run_out(db, latest) if latest else None))
    return output


@app.get("/api/v1/research-projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(ResearchProject, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    latest = db.scalar(select(ResearchRun).where(ResearchRun.project_id == project.id).order_by(desc(ResearchRun.started_at), desc(ResearchRun.id)))
    return ProjectOut(id=project.id, title=project.title, original_question=project.original_question, created_at=project.created_at, latest_run=run_out(db, latest) if latest else None)


@app.get("/api/v1/research-runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(ResearchRun, run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    project = db.get(ResearchProject, run.project_id)
    base = run_out(db, run).model_dump()
    plan_items = list(db.scalars(select(PlanItem).where(PlanItem.run_id == run_id).order_by(PlanItem.item_type, PlanItem.position)).all())
    conclusions = list(db.scalars(select(Conclusion).where(Conclusion.run_id == run_id)).all())
    return RunDetail(**base, question=project.original_question, plan_items=[item.text for item in plan_items], conclusions=[conclusion_out(db, item) for item in conclusions])


@app.get("/api/v1/research-runs/{run_id}/events", response_model=list[RunEventOut])
def get_events(run_id: str, db: Session = Depends(get_db)):
    if not db.get(ResearchRun, run_id):
        raise HTTPException(404, "Research run not found")
    events = list(db.scalars(select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.occurred_at)).all())
    return [RunEventOut(stage=item.stage, status=item.status, message=item.message, metadata=json.loads(item.metadata_json), occurred_at=item.occurred_at) for item in events]


@app.get("/api/v1/research-runs/{run_id}/sources", response_model=list[SourceOut])
def get_sources(run_id: str, db: Session = Depends(get_db)):
    snapshots = list(db.scalars(select(SourceSnapshot).where(SourceSnapshot.run_id == run_id).order_by(SourceSnapshot.retrieved_at)).all())
    return [source_out(db, item) for item in snapshots]


@app.get("/api/v1/research-runs/{run_id}/claims", response_model=list[ClaimOut])
def get_claims(run_id: str, db: Session = Depends(get_db)):
    claims = list(db.scalars(select(Claim).where(Claim.run_id == run_id).order_by(Claim.topic)).all())
    return [claim_out(db, item) for item in claims]


@app.get("/api/v1/research-runs/{run_id}/assessments", response_model=list[AssessmentOut])
def get_assessments(run_id: str, db: Session = Depends(get_db)):
    assessments = list(
        db.scalars(select(EvidenceAssessment).join(Claim, EvidenceAssessment.left_claim_id == Claim.id).where(Claim.run_id == run_id)).all()
    )
    return [assessment_out(item) for item in assessments]


@app.get("/api/v1/conclusions/{conclusion_id}/trace", response_model=TraceOut)
def get_conclusion_trace(conclusion_id: str, db: Session = Depends(get_db)):
    conclusion = db.get(Conclusion, conclusion_id)
    if not conclusion:
        raise HTTPException(404, "Conclusion not found")
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


@app.post("/api/v1/research-runs/{run_id}/retry", response_model=RunOut, status_code=202)
def retry_run(run_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = db.get(ResearchRun, run_id)
    if not run:
        raise HTTPException(404, "Research run not found")
    if run.status not in {"failed", "partial"}:
        raise HTTPException(409, "Only failed or partial runs can be retried")
    retry = create_retry_run(db, run)
    background_tasks.add_task(run_research, retry.id)
    return run_out(db, retry)
