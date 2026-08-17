import json
import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import (
    Claim,
    Conclusion,
    ConclusionClaim,
    EvidenceAssessment,
    ResearchProject,
    ResearchRun,
    RunEvent,
    Source,
    SourceSnapshot,
)


@pytest.fixture(autouse=True)
def mock_run_tasks(monkeypatch):
    monkeypatch.setattr("app.main.run_research", lambda run_id: None)
    monkeypatch.setattr("app.services.run_research", lambda run_id: None)


def test_idor_cross_user_run_access_rejected(db_session):
    """User B cannot access User A's research run details, events, sources, claims, assessments, or traces."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # Create Project & Run for User A
        proj_a = ResearchProject(
            title="User A Top Secret",
            original_question="User A Secret Question",
            user_id="usr_user_a",
            project_type="web",
        )
        db_session.add(proj_a)
        db_session.commit()

        run_a = ResearchRun(
            project_id=proj_a.id,
            status="completed",
            provider_name="bedrock",
            model_name="claude-3-5-sonnet",
        )
        db_session.add(run_a)
        db_session.commit()

        event_a = RunEvent(run_id=run_a.id, stage="planning", status="completed", message="Plan created")
        source_a = Source(canonical_url="https://secret.corp/doc", title="Secret Doc")
        db_session.add_all([event_a, source_a])
        db_session.commit()

        snap_a = SourceSnapshot(source_id=source_a.id, run_id=run_a.id, content_hash="hash1", cleaned_text="Secret text")
        db_session.add(snap_a)
        db_session.commit()

        claim_a = Claim(
            run_id=run_a.id,
            snapshot_id=snap_a.id,
            topic="Secret Topic",
            statement="Secret Statement",
            classification="impact",
            confidence="high",
            exact_excerpt="Secret text",
        )
        db_session.add(claim_a)
        db_session.commit()

        conclusion_a = Conclusion(run_id=run_a.id, statement="Top Secret Conclusion", confidence="high")
        db_session.add(conclusion_a)
        db_session.commit()

        link_a = ConclusionClaim(conclusion_id=conclusion_a.id, claim_id=claim_a.id, role="supports")
        db_session.add(link_a)
        db_session.commit()

        # User A headers & User B headers
        headers_a = {"Authorization": "Bearer mock-user-user_a"}
        headers_b = {"Authorization": "Bearer mock-user-user_b"}

        # 1. User A can access their own run and sub-resources
        assert client.get(f"/api/v1/research-runs/{run_a.id}", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}/events", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}/sources", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}/claims", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/conclusions/{conclusion_a.id}/trace", headers=headers_a).status_code == 200

        # 2. User B attempting to access User A's resources MUST be blocked with 404 (IDOR protection)
        assert client.get(f"/api/v1/research-projects/{proj_a.id}/runs", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/events", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/sources", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/claims", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/assessments", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/conclusions/{conclusion_a.id}/trace", headers=headers_b).status_code == 404

    finally:
        app.dependency_overrides.clear()
