from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Claim, Conclusion, ConclusionClaim, Source, SourceSnapshot
from app.services import canonicalize_url, create_project_and_run, create_retry_run


def test_canonicalize_url_removes_tracking_and_fragments():
    assert canonicalize_url("HTTPS://Example.com/report/?utm_source=newsletter&year=2026#section") == "https://example.com/report?year=2026"
    assert canonicalize_url("https://example.com:443/report?b=2&gclid=tracking&a=1") == "https://example.com/report?a=1&b=2"


def test_retry_creates_an_immutable_new_run(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'retry.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    _, original = create_project_and_run(session, "How is AI transforming retail operations?", "Retail AI")
    original.status = "failed"
    session.commit()

    retry = create_retry_run(session, original)
    assert retry.id != original.id
    assert retry.project_id == original.project_id
    assert retry.status == "queued"
    session.close()


def test_project_run_and_evidence_records_persist(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    project, run = create_project_and_run(
        session,
        "How is AI transforming retail operations?",
        "Retail AI research",
    )
    source = Source(canonical_url="https://example.com/research", title="Example research", publisher="example.com")
    session.add(source)
    session.flush()
    snapshot = SourceSnapshot(
        source_id=source.id,
        run_id=run.id,
        content_hash="a" * 64,
        cleaned_text="AI improves demand forecasts when historical sales data is reliable.",
    )
    session.add(snapshot)
    session.flush()
    claim = Claim(
        run_id=run.id,
        snapshot_id=snapshot.id,
        topic="demand forecasting",
        statement="AI can improve demand forecasting when reliable historical data is available.",
        classification="impact",
        confidence="medium",
        exact_excerpt="AI improves demand forecasts when historical sales data is reliable.",
        excerpt_start=0,
        excerpt_end=68,
    )
    session.add(claim)
    session.flush()
    conclusion = Conclusion(
        run_id=run.id,
        statement="AI forecasting benefits depend on reliable historical data.",
        confidence="medium",
        limitations="One source only in this unit test.",
    )
    session.add(conclusion)
    session.flush()
    session.add(ConclusionClaim(conclusion_id=conclusion.id, claim_id=claim.id, role="supports"))
    session.commit()

    stored_claim = session.scalar(select(Claim).where(Claim.run_id == run.id))
    stored_link = session.scalar(select(ConclusionClaim).where(ConclusionClaim.conclusion_id == conclusion.id))
    assert project.original_question.startswith("How is AI")
    assert stored_claim is not None
    assert stored_claim.snapshot_id == snapshot.id
    assert stored_link.claim_id == stored_claim.id
    session.close()
