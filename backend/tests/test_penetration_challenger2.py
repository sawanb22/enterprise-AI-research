import io
import os
import re
import anyio
import pymupdf
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings, get_settings
from app.database import get_db
from app.models import ResearchProject, Document
from app.auth.jwt_verifier import SupabaseJWTVerifier, _token_cache


@pytest.fixture(autouse=True)
def mock_run_tasks(monkeypatch):
    """Disable background tasks during penetration testing."""
    monkeypatch.setattr("app.main.run_research", lambda run_id: None)
    monkeypatch.setattr("app.services.run_research", lambda run_id: None)


# ==============================================================================
# 1. SECRET ISOLATION IN FRONTEND DIST BUNDLE
# ==============================================================================

def test_frontend_dist_zero_secret_leakage():
    """Empirically asserts that frontend/dist contains zero server secrets or db URLs."""
    dist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
    assert os.path.exists(dist_dir), "frontend/dist directory must exist"

    prohibited_patterns = [
        re.compile(r"AWS_BEARER_TOKEN_BEDROCK", re.I),
        re.compile(r"TAVILY_API_KEY", re.I),
        re.compile(r"DATABASE_URL", re.I),
        re.compile(r"SUPABASE_SERVICE_ROLE_KEY", re.I),
        re.compile(r"SUPABASE_JWT_SECRET", re.I),
        re.compile(r"postgresql://", re.I),
        re.compile(r"AWS_SECRET_ACCESS_KEY", re.I),
    ]

    scanned_files = 0
    for root, _, files in os.walk(dist_dir):
        for file in files:
            fpath = os.path.join(root, file)
            with open(fpath, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")
            scanned_files += 1
            for pat in prohibited_patterns:
                matches = pat.findall(content)
                assert len(matches) == 0, f"Leaked secret pattern {pat.pattern} found in {file}: {matches}"

    assert scanned_files >= 3, f"Expected at least 3 dist files scanned, found {scanned_files}"


# ==============================================================================
# 2. CORS PREFLIGHT & REGEX ADVERSARIAL STRESS TESTING
# ==============================================================================

@pytest.mark.parametrize("origin,expected_allowed", [
    ("http://localhost:5173", True),
    ("https://evidence-lab-frontend-git-main-sawan.vercel.app", True),
    ("https://random-preview-123.vercel.app", True),
    ("https://evil-hacker.com", False),
    ("https://evil-vercel.app.attacker.com", False),
    ("http://foo.vercel.app", False),
    ("null", False),
])
def test_cors_preflight_and_origin_enforcement(origin, expected_allowed):
    """Verifies that CORS origins and preflight requests strictly enforce whitelist and regex."""
    client = TestClient(app)
    # Test GET request
    resp_get = client.get("/api/v1/health", headers={"Origin": origin})
    assert resp_get.status_code == 200
    allow_origin_header = resp_get.headers.get("access-control-allow-origin")

    if expected_allowed:
        assert allow_origin_header == origin
        assert resp_get.headers.get("access-control-allow-credentials") == "true"
    else:
        assert allow_origin_header is None

    # Test OPTIONS preflight request
    resp_opt = client.options(
        "/api/v1/research-projects",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    opt_allow_origin = resp_opt.headers.get("access-control-allow-origin")

    if expected_allowed:
        assert resp_opt.status_code == 200
        assert opt_allow_origin == origin
        assert "POST" in resp_opt.headers.get("access-control-allow-methods", "")
    else:
        assert resp_opt.status_code == 400
        assert opt_allow_origin is None


# ==============================================================================
# 3. SQL & VECTOR INJECTION RESISTANCE
# ==============================================================================

@pytest.mark.parametrize("payload", [
    "' OR '1'='1",
    "'; DROP TABLE research_projects; --",
    "1' UNION SELECT 1, 'admin', 'pass' --",
    "\" OR \"\"=\"",
    "1; SELECT pg_sleep(1); --",
    "\\x00' OR 1=1 --",
])
def test_sql_injection_resistance_on_all_id_parameters(db_session, payload):
    """Asserts that SQL injection payloads in URL paths return 404 or 422, never 500 or SQL errors."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        endpoints = [
            f"/api/v1/research-projects/{payload}",
            f"/api/v1/research-projects/{payload}/runs",
            f"/api/v1/research-runs/{payload}",
            f"/api/v1/research-runs/{payload}/events",
            f"/api/v1/research-runs/{payload}/sources",
            f"/api/v1/research-runs/{payload}/claims",
            f"/api/v1/research-runs/{payload}/assessments",
            f"/api/v1/conclusions/{payload}/trace",
            f"/api/v1/documents/{payload}",
            f"/api/v1/rag-reports/{payload}",
        ]
        for ep in endpoints:
            resp = client.get(ep, headers={"X-Test-User-Id": "usr_challenger2"})
            assert resp.status_code in (404, 422), f"Endpoint {ep} failed with status {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 4. PDF INGESTION & MAGIC BYTE FUZZING
# ==============================================================================

def test_pdf_upload_security_controls(db_session):
    """Tests extension validation, magic bytes check, and path traversal defense in PDF upload."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        project = ResearchProject(
            title="PDF Security Test Project",
            original_question="Fuzzing ingestion",
            user_id="usr_pdf_tester",
            project_type="rag",
        )
        db_session.add(project)
        db_session.commit()
        proj_id = project.id

        headers = {"X-Test-User-Id": "usr_pdf_tester"}

        # 4.1 Non-PDF extension rejection
        bad_ext_files = {"file": ("malicious.exe", io.BytesIO(b"%PDF-1.4\nvalid header"), "application/x-msdownload")}
        resp = client.post(f"/api/v1/projects/{proj_id}/documents", files=bad_ext_files, headers=headers)
        assert resp.status_code == 400
        assert "Only PDF" in resp.json().get("detail", "")

        # 4.2 Non-PDF magic bytes rejection (disguised as .pdf)
        fake_pdf_files = {"file": ("exploit.pdf", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "application/pdf")}
        resp = client.post(f"/api/v1/projects/{proj_id}/documents", files=fake_pdf_files, headers=headers)
        assert resp.status_code == 400
        assert "Invalid file format" in resp.json().get("detail", "")

        # 4.3 HTML disguised as PDF
        html_files = {"file": ("xss.pdf", io.BytesIO(b"<!DOCTYPE html><html><body>alert(1)</body></html>"), "application/pdf")}
        resp = client.post(f"/api/v1/projects/{proj_id}/documents", files=html_files, headers=headers)
        assert resp.status_code == 400
        assert "Invalid file format" in resp.json().get("detail", "")

        # 4.4 Path traversal in filename sanitized / stored by UUID
        pdf_gen = pymupdf.open()
        pdf_gen.new_page()
        valid_pdf_payload = pdf_gen.tobytes()
        pdf_gen.close()

        traversal_fn = "../../../etc/cron.d/backdoor.pdf"
        traversal_files = {"file": (traversal_fn, io.BytesIO(valid_pdf_payload), "application/pdf")}
        resp = client.post(f"/api/v1/projects/{proj_id}/documents", files=traversal_files, headers=headers)
        assert resp.status_code in (200, 201)
        doc_data = resp.json()
        assert doc_data["id"] is not None
        # Verify file is stored inside data/uploads with UUID, not outside
        doc = db_session.get(Document, doc_data["id"])
        assert doc is not None
        expected_path = Path("./data/uploads").resolve() / f"{doc.id}.pdf"
        assert expected_path.exists()

    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 5. ENVIRONMENT GATING IN PRODUCTION MODE
# ==============================================================================

def test_production_environment_blocks_test_headers_and_mock_tokens(monkeypatch, db_session):
    """Verifies that in production mode, X-Test-User-Id and mock-user-* tokens are blocked."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        _token_cache.clear()
        monkeypatch.setenv("ENVIRONMENT", "production")
        prod_settings = Settings(environment="production")

        # 1. Test X-Test-User-Id blocked in production
        resp_header = client.get("/api/v1/auth/me", headers={"X-Test-User-Id": "usr_attacker"})
        assert resp_header.status_code == 401, f"Expected 401 in production for X-Test-User-Id, got {resp_header.status_code}"

        # 2. Test mock-user-* token blocked in production
        verifier = SupabaseJWTVerifier(prod_settings)
        user = anyio.run(verifier.verify_token, "Bearer mock-user-admin")
        assert user is None, "mock-user-* token must return None in production"

        user2 = anyio.run(verifier.verify_token, "Bearer test-token-victim")
        assert user2 is None, "test-token-* must return None in production"

        resp_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer mock-user-admin"})
        assert resp_token.status_code == 401, f"Expected 401 in production for mock token, got {resp_token.status_code}"
    finally:
        _token_cache.clear()
        app.dependency_overrides.clear()
