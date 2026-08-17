import io
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from app.auth import verify_api_key
from app.config import Settings
from app.main import app
from app.rate_limiter import SlidingWindowRateLimiter, limiter, rate_limit


def test_rate_limiter_window_and_headers():
    test_limiter = SlidingWindowRateLimiter()
    key = "test_ip:test_endpoint"

    # Allow up to 3 requests
    allowed1, rem1, retry1 = test_limiter.check(key, max_requests=3, window_seconds=60)
    assert allowed1 is True
    assert rem1 == 2

    allowed2, rem2, retry2 = test_limiter.check(key, max_requests=3, window_seconds=60)
    assert allowed2 is True
    assert rem2 == 1

    allowed3, rem3, retry3 = test_limiter.check(key, max_requests=3, window_seconds=60)
    assert allowed3 is True
    assert rem3 == 0

    # 4th request must be blocked
    allowed4, rem4, retry4 = test_limiter.check(key, max_requests=3, window_seconds=60)
    assert allowed4 is False
    assert rem4 == 0
    assert retry4 > 0


def test_rate_limiter_endpoint_429():
    test_app = FastAPI()
    limiter.reset()

    @test_app.post("/test-expensive-ai", dependencies=[Depends(rate_limit(max_requests=3, window_seconds=60))])
    def expensive_endpoint():
        return {"status": "ok"}

    with TestClient(test_app) as client:
        r1 = client.post("/test-expensive-ai")
        assert r1.status_code == 200

        r2 = client.post("/test-expensive-ai")
        assert r2.status_code == 200

        r3 = client.post("/test-expensive-ai")
        assert r3.status_code == 200

        # 4th call exceeds limit -> 429
        r4 = client.post("/test-expensive-ai")
        assert r4.status_code == 429
        assert "Retry-After" in r4.headers
        assert "Rate limit exceeded" in r4.json()["detail"]
    limiter.reset()


def test_upload_rejects_non_pdf_extension(db_session):
    from app.database import get_db
    from app.models import ResearchProject
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        project = ResearchProject(title="Sec Non PDF", original_question="Sec Question")
        db_session.add(project)
        db_session.commit()

        client = TestClient(app)
        files = {"file": ("malicious.exe", b"%PDF-1.4 Fake PDF", "application/pdf")}
        resp = client.post(f"/api/v1/projects/{project.id}/documents", files=files)
        assert resp.status_code == 400
        assert "Only PDF documents are supported" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_upload_rejects_invalid_pdf_magic_bytes(db_session):
    from app.database import get_db
    from app.models import ResearchProject
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        project = ResearchProject(title="Sec Test", original_question="Sec Question")
        db_session.add(project)
        db_session.commit()

        client = TestClient(app)
        files = {"file": ("document.pdf", b"NOT_A_PDF_HEADER_CONTENT", "application/pdf")}
        resp = client.post(f"/api/v1/projects/{project.id}/documents", files=files)
        assert resp.status_code == 400
        assert "Invalid file format" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_upload_rejects_oversized_payload(db_session, monkeypatch):
    from app.config import get_settings
    from app.database import get_db
    from app.models import ResearchProject
    app.dependency_overrides[get_db] = lambda: db_session

    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_mb", 1)

    try:
        project = ResearchProject(title="Oversize Test", original_question="Sec Question")
        db_session.add(project)
        db_session.commit()

        client = TestClient(app)
        oversized_content = b"%PDF-1.5 " + b"X" * (2 * 1024 * 1024)
        files = {"file": ("huge.pdf", oversized_content, "application/pdf")}
        resp = client.post(f"/api/v1/projects/{project.id}/documents", files=files)
        assert resp.status_code == 413
        assert "File exceeds maximum allowed size" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_auth_verification_modes():
    # 1. Dev mode (no key configured) -> Allowed
    dev_settings = Settings(api_auth_key=None)
    assert verify_api_key(header_key=None, bearer_creds=None, settings=dev_settings) is True

    # 2. Configured key -> valid key passes
    prod_settings = Settings(api_auth_key="secret-api-key-12345")
    assert verify_api_key(header_key="secret-api-key-12345", bearer_creds=None, settings=prod_settings) is True

    # 3. Configured key -> invalid key raises 401
    with pytest.raises(HTTPException) as exc:
        verify_api_key(header_key="wrong-key", bearer_creds=None, settings=prod_settings)
    assert exc.value.status_code == 401


@pytest.mark.anyio
async def test_local_jwt_cryptographic_verification():
    import time
    import jwt
    from app.auth.jwt_verifier import SupabaseJWTVerifier
    from app.config import Settings

    secret = "super-secret-test-jwt-key-for-local-signing-12345"
    settings = Settings(
        supabase_jwt_secret=secret,
        supabase_url="https://testproject.supabase.co",
    )
    verifier = SupabaseJWTVerifier(settings=settings)

    # 1. Valid signed HS256 JWT
    valid_payload = {
        "sub": "user-uuid-12345",
        "email": "researcher@modus.com",
        "aud": "authenticated",
        "iss": "https://testproject.supabase.co/auth/v1",
        "exp": int(time.time()) + 3600,
        "user_metadata": {"full_name": "Dr. Researcher"},
    }
    valid_token = jwt.encode(valid_payload, secret, algorithm="HS256")
    user = await verifier.verify_token(valid_token)
    assert user is not None
    assert user.id == "user-uuid-12345"
    assert user.email == "researcher@modus.com"
    assert user.full_name == "Dr. Researcher"

    # 2. Forged signature -> Rejected (None)
    forged_token = jwt.encode(valid_payload, "wrong-signature-key", algorithm="HS256")
    user_forged = await verifier.verify_token(forged_token)
    assert user_forged is None

    # 3. Expired token -> Rejected (None)
    expired_payload = {**valid_payload, "exp": int(time.time()) - 100}
    expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")
    user_expired = await verifier.verify_token(expired_token)
    assert user_expired is None

    # 4. Wrong audience -> Rejected (None)
    wrong_aud_payload = {**valid_payload, "aud": "admin_service_role"}
    wrong_aud_token = jwt.encode(wrong_aud_payload, secret, algorithm="HS256")
    user_wrong_aud = await verifier.verify_token(wrong_aud_token)
    assert user_wrong_aud is None


def test_bootstrap_security_headers_and_batching(db_session):
    """GET /api/v1/workspace/bootstrap returns strict anti-proxy-bleed security headers."""
    from app.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        headers = {"Authorization": "Bearer mock-user-header-check"}
        resp = client.get("/api/v1/workspace/bootstrap", headers=headers)
        assert resp.status_code == 200
        assert "private" in resp.headers.get("Cache-Control", "")
        assert "Authorization" in resp.headers.get("Vary", "")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        data = resp.json()
        assert data["user"]["id"] == "usr_header-check"
    finally:
        app.dependency_overrides.clear()
