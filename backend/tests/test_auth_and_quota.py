import pytest
from fastapi.testclient import TestClient

from app.auth.models import UserQuota
from app.auth.schemas import AuthenticatedUser
from app.auth.service import QuotaService
from app.database import get_db
from app.main import app
from app.models import ResearchProject


from app.rate_limiter import limiter


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Automatically mock long-running research and reset sliding window rate limiter."""
    monkeypatch.setattr("app.main.run_research", lambda run_id: None)
    monkeypatch.setattr("app.services.run_research", lambda run_id: None)
    limiter.reset()
    yield
    limiter.reset()


def test_unauthenticated_research_rejected(db_session):
    """Attempting to create research project without bearer auth returns 401."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        resp = client.post(
            "/api/v1/research-projects",
            json={"question": "Unauthenticated test question", "title": "Test"},
        )
        assert resp.status_code == 401
        assert "Authentication required" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_authenticated_research_success_and_quota_increment(db_session):
    """Authenticated user creates research project, consumes 1 run allocation."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        headers = {"Authorization": "Bearer mock-user-alice"}
        resp = client.post(
            "/api/v1/research-projects",
            json={"question": "How do solid-state batteries compare to lithium-ion?", "title": "Battery Study"},
            headers=headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["project_id"] is not None

        # Check quota status
        quota_resp = client.get("/api/v1/auth/quota", headers=headers)
        assert quota_resp.status_code == 200
        quota_data = quota_resp.json()
        assert quota_data["total_runs_used"] == 1
        assert quota_data["max_free_runs"] == 5
        assert quota_data["remaining_runs"] == 4
        assert quota_data["is_quota_exhausted"] is False
    finally:
        app.dependency_overrides.clear()


def test_5_messages_lifetime_limit_exhaustion(db_session):
    """User can submit up to 5 research inquiries; 6th attempt is blocked with HTTP 402."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        headers = {"Authorization": "Bearer mock-user-quota-pilot"}

        # Run 5 inquiries
        for i in range(1, 6):
            resp = client.post(
                "/api/v1/research-projects",
                json={"question": f"Inquiry number {i} on quantum computing", "title": f"Inquiry {i}"},
                headers=headers,
            )
            assert resp.status_code == 202, f"Inquiry {i} failed: {resp.text}"

        # Check quota: 5/5 used
        quota_resp = client.get("/api/v1/auth/quota", headers=headers)
        assert quota_resp.status_code == 200
        assert quota_resp.json()["total_runs_used"] == 5
        assert quota_resp.json()["remaining_runs"] == 0
        assert quota_resp.json()["is_quota_exhausted"] is True

        # 6th attempt MUST fail with HTTP 402 Payment Required / Quota Exceeded
        blocked_resp = client.post(
            "/api/v1/research-projects",
            json={"question": "6th attempt that should be blocked", "title": "Blocked 6th Run"},
            headers=headers,
        )
        assert blocked_resp.status_code == 402
        assert "Pilot quota reached" in blocked_resp.json()["detail"]
        assert "5 free research inquiries" in blocked_resp.json()["detail"]

    finally:
        app.dependency_overrides.clear()


def test_user_project_isolation(db_session):
    """Users only see their own projects and cannot access other users' projects."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        headers_user_a = {"Authorization": "Bearer mock-user-isolated-a"}
        headers_user_b = {"Authorization": "Bearer mock-user-isolated-b"}

        # User A creates Project A
        resp_a = client.post(
            "/api/v1/research-projects",
            json={"question": "User A Private Research", "title": "Project A"},
            headers=headers_user_a,
        )
        assert resp_a.status_code == 202
        proj_a_id = resp_a.json()["project_id"]

        # User B creates Project B
        resp_b = client.post(
            "/api/v1/research-projects",
            json={"question": "User B Private Research", "title": "Project B"},
            headers=headers_user_b,
        )
        assert resp_b.status_code == 202
        proj_b_id = resp_b.json()["project_id"]

        # User A lists projects -> sees Project A, NOT Project B
        list_a = client.get("/api/v1/research-projects", headers=headers_user_a).json()
        list_a_ids = [p["id"] for p in list_a]
        assert proj_a_id in list_a_ids
        assert proj_b_id not in list_a_ids

        # User B lists projects -> sees Project B, NOT Project A
        list_b = client.get("/api/v1/research-projects", headers=headers_user_b).json()
        list_b_ids = [p["id"] for p in list_b]
        assert proj_b_id in list_b_ids
        assert proj_a_id not in list_b_ids

        # User A tries to GET Project B directly -> 404
        get_b_by_a = client.get(f"/api/v1/research-projects/{proj_b_id}", headers=headers_user_a)
        assert get_b_by_a.status_code == 404

    finally:
        app.dependency_overrides.clear()


def test_auth_me_and_quota_endpoint(db_session):
    """GET /api/v1/auth/me returns authenticated user identity and quota."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        headers = {"Authorization": "Bearer mock-user-tester"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["id"] == "usr_tester"
        assert data["user"]["email"] == "tester@example.com"
        assert data["quota"]["max_free_runs"] == 5
        assert data["quota"]["total_runs_used"] == 0
        assert data["quota"]["remaining_runs"] == 5
    finally:
        app.dependency_overrides.clear()
