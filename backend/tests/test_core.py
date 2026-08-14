from sqlalchemy import select

from app.models import Claim, Conclusion, ConclusionClaim, Source, SourceSnapshot
from app.services import canonicalize_url, create_project_and_run, create_retry_run


def test_canonicalize_url_removes_tracking_and_fragments():
    assert canonicalize_url("HTTPS://Example.com/report/?utm_source=newsletter&year=2026#section") == "https://example.com/report?year=2026"
    assert canonicalize_url("https://example.com:443/report?b=2&gclid=tracking&a=1") == "https://example.com/report?a=1&b=2"


def test_retry_creates_an_immutable_new_run(db_session):
    _, original = create_project_and_run(db_session, "How is AI transforming retail operations?", "Retail AI")
    original.status = "failed"
    db_session.flush()

    retry = create_retry_run(db_session, original)
    assert retry.id != original.id
    assert retry.project_id == original.project_id
    assert retry.status == "queued"


def test_project_run_and_evidence_records_persist(db_session):
    project, run = create_project_and_run(
        db_session,
        "How is AI transforming retail operations?",
        "Retail AI research",
    )
    source = Source(canonical_url="https://example.com/research", title="Example research", publisher="example.com")
    db_session.add(source)
    db_session.flush()
    snapshot = SourceSnapshot(
        source_id=source.id,
        run_id=run.id,
        content_hash="a" * 64,
        cleaned_text="AI improves demand forecasts when historical sales data is reliable.",
    )
    db_session.add(snapshot)
    db_session.flush()
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
    db_session.add(claim)
    db_session.flush()
    conclusion = Conclusion(
        run_id=run.id,
        statement="AI forecasting benefits depend on reliable historical data.",
        confidence="medium",
        limitations="One source only in this unit test.",
    )
    db_session.add(conclusion)
    db_session.flush()
    db_session.add(ConclusionClaim(conclusion_id=conclusion.id, claim_id=claim.id, role="supports"))
    db_session.flush()

    stored_claim = db_session.scalar(select(Claim).where(Claim.run_id == run.id))
    stored_link = db_session.scalar(select(ConclusionClaim).where(ConclusionClaim.conclusion_id == conclusion.id))
    assert project.original_question.startswith("How is AI")
    assert stored_claim is not None
    assert stored_claim.snapshot_id == snapshot.id
    assert stored_link.claim_id == stored_claim.id


def test_list_project_runs_endpoint(db_session):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        project, run1 = create_project_and_run(db_session, "Question for project runs endpoint", "Project Test")
        retry = create_retry_run(db_session, run1)
        project_id = project.id
        run1_id = run1.id
        retry_id = retry.id
        db_session.flush()

        client = TestClient(app)
        resp = client.get(f"/api/v1/research-projects/{project_id}/runs")
        assert resp.status_code == 200
        runs = resp.json()
        assert len(runs) >= 2
        assert {run1_id, retry_id}.issubset({r["id"] for r in runs})
    finally:
        app.dependency_overrides.clear()


def test_endpoints_return_404_on_missing_run(db_session):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        client = TestClient(app)
        missing_id = "non-existent-run-id-12345"
        assert client.get(f"/api/v1/research-runs/{missing_id}/sources").status_code == 404
        assert client.get(f"/api/v1/research-runs/{missing_id}/claims").status_code == 404
        assert client.get(f"/api/v1/research-runs/{missing_id}/assessments").status_code == 404
        assert client.get(f"/api/v1/research-runs/{missing_id}/events").status_code == 404
        assert client.get(f"/api/v1/research-runs/{missing_id}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_valid_excerpt_matches_smart_quotes_and_whitespace():
    from app.services import _valid_excerpt

    # Source has curly quotes
    source = "The report concludes that “smart automated inventory forecasting” dramatically reduces overstock."
    # Excerpt has standard quotes
    excerpt_standard_quotes = '"smart automated inventory forecasting" dramatically reduces overstock.'
    res = _valid_excerpt(source, excerpt_standard_quotes)
    assert res is not None
    assert res[1] >= 0

    # Excerpt has differing whitespace / newline
    source_multiline = "Enterprise retailers reported a  30% reduction   in logistics costs during Q4."
    excerpt_single_space = "Enterprise retailers reported a 30% reduction in logistics costs during Q4."
    res_ws = _valid_excerpt(source_multiline, excerpt_single_space)
    assert res_ws is not None


def test_select_comparison_pairs_falls_back_to_cross_source_when_topics_differ():
    from app.services import _select_comparison_pairs

    c1 = Claim(id="c1", run_id="r1", snapshot_id="s1", topic="Automated replenishment", statement="Replenishment is automated.", classification="impact", confidence="high", exact_excerpt="Replenishment is automated.", excerpt_start=0, excerpt_end=28)
    c2 = Claim(id="c2", run_id="r1", snapshot_id="s2", topic="Inventory optimization", statement="Inventory optimization cuts cost.", classification="opportunity", confidence="medium", exact_excerpt="Inventory optimization cuts cost.", excerpt_start=0, excerpt_end=34)
    c3 = Claim(id="c3", run_id="r1", snapshot_id="s3", topic="Demand forecasting", statement="Demand forecasting improves margin.", classification="impact", confidence="high", exact_excerpt="Demand forecasting improves margin.", excerpt_start=0, excerpt_end=35)

    pairs = _select_comparison_pairs([c1, c2, c3], max_pairs=3)
    assert len(pairs) == 3
    for left, right in pairs:
        assert left.snapshot_id != right.snapshot_id
