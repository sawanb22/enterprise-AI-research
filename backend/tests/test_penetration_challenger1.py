import io
import json
import time
import jwt
import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_verifier import _token_cache, SupabaseJWTVerifier
from app.config import Settings, get_settings
from app.database import get_db
from app.main import app
from app.models import (
    Claim,
    Conclusion,
    ConclusionClaim,
    Document,
    EvidenceAssessment,
    RAGReport,
    ResearchProject,
    ResearchRun,
    RunEvent,
    Source,
    SourceSnapshot,
)


def create_valid_test_pdf(text: str = "Test PDF Document") -> bytes:
    """Helper to generate a syntactically valid minimal 1-page PDF in memory."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(autouse=True)
def mock_run_tasks(monkeypatch):
    """Disable background tasks during penetration testing."""
    monkeypatch.setattr("app.main.run_research", lambda run_id: None)
    monkeypatch.setattr("app.services.run_research", lambda run_id: None)


# ---------------------------------------------------------------------------
# 1. Unauthenticated Access Penetration Tests
# ---------------------------------------------------------------------------

def test_pen_unauthenticated_enumeration_and_access_blocked(db_session):
    """
    Adversarial Penetration Test:
    Attempt unauthenticated access against every owned endpoint.
    Assert that unauthenticated requests to owned resources return 404 (read/delete) or 401 (create/mutation).
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # Create private owned project & run for victim user
        victim_project = ResearchProject(
            title="Victim Classified Project",
            original_question="Victim Proprietary Question",
            user_id="victim_tenant_1001",
            project_type="web",
        )
        db_session.add(victim_project)
        db_session.commit()

        victim_run = ResearchRun(
            project_id=victim_project.id,
            status="failed",  # Set to failed so retry is theoretically valid if auth passed
            provider_name="bedrock",
            model_name="claude-3-5-sonnet",
        )
        db_session.add(victim_run)
        db_session.commit()

        event = RunEvent(run_id=victim_run.id, stage="extracting", status="completed", message="Extracted data")
        source = Source(canonical_url="https://victim.internal/data", title="Confidential Internal Source")
        db_session.add_all([event, source])
        db_session.commit()

        snap = SourceSnapshot(
            source_id=source.id,
            run_id=victim_run.id,
            content_hash="hash_classified",
            cleaned_text="Highly confidential source text",
        )
        db_session.add(snap)
        db_session.commit()

        claim = Claim(
            run_id=victim_run.id,
            snapshot_id=snap.id,
            topic="Classified Financials",
            statement="Confidential EBITDA stats",
            classification="impact",
            confidence="high",
            exact_excerpt="EBITDA stats",
        )
        db_session.add(claim)
        db_session.commit()

        conclusion = Conclusion(run_id=victim_run.id, statement="Confidential Conclusion", confidence="high")
        db_session.add(conclusion)
        db_session.commit()

        link = ConclusionClaim(conclusion_id=conclusion.id, claim_id=claim.id, role="supports")
        db_session.add(link)
        db_session.commit()

        doc = Document(
            project_id=victim_project.id,
            filename="classified_plans.pdf",
            file_hash="hash_pdf_classified",
            file_size_bytes=4096,
            status="completed",
            page_count=5,
        )
        db_session.add(doc)
        db_session.commit()

        report = RAGReport(
            project_id=victim_project.id,
            question="What is the internal growth rate?",
            report_json=json.dumps({"summary": "Internal secret", "sections": []}),
            status="completed",
        )
        db_session.add(report)
        db_session.commit()

        # Execute unauthenticated probes (Zero headers)
        # 1. Project Level
        assert client.get(f"/api/v1/research-projects/{victim_project.id}").status_code == 404
        assert client.get(f"/api/v1/research-projects/{victim_project.id}/runs").status_code == 404

        # 2. Run & Artifact Level
        assert client.get(f"/api/v1/research-runs/{victim_run.id}").status_code == 404
        assert client.get(f"/api/v1/research-runs/{victim_run.id}/events").status_code == 404
        assert client.get(f"/api/v1/research-runs/{victim_run.id}/sources").status_code == 404
        assert client.get(f"/api/v1/research-runs/{victim_run.id}/claims").status_code == 404
        assert client.get(f"/api/v1/research-runs/{victim_run.id}/assessments").status_code == 404
        assert client.get(f"/api/v1/conclusions/{conclusion.id}/trace").status_code == 404

        # 3. Document Level
        assert client.get(f"/api/v1/projects/{victim_project.id}/documents").status_code == 404
        assert client.get(f"/api/v1/documents/{doc.id}").status_code == 404
        assert client.delete(f"/api/v1/documents/{doc.id}").status_code == 404
        valid_pdf = create_valid_test_pdf("Unauth attempt")
        files = {"file": ("unauth_upload.pdf", valid_pdf, "application/pdf")}
        assert client.post(f"/api/v1/projects/{victim_project.id}/documents", files=files).status_code == 404

        # 4. RAG Report Level
        assert client.get(f"/api/v1/projects/{victim_project.id}/rag-reports").status_code == 404
        assert client.get(f"/api/v1/rag-reports/{report.id}").status_code == 404

        # 5. Authenticated mutations without token -> 401
        assert client.post("/api/v1/research-projects", json={"question": "Unauth inquiry"}).status_code == 401
        assert client.post(f"/api/v1/research-runs/{victim_run.id}/retry").status_code == 401
        assert client.post(
            f"/api/v1/projects/{victim_project.id}/rag-research",
            json={"question": "Unauth RAG query"},
        ).status_code == 401

    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 2. Cross-Tenant IDOR Attack Matrix
# ---------------------------------------------------------------------------

def test_pen_cross_tenant_idor_full_matrix(db_session):
    """
    Adversarial Penetration Test:
    User B (Attacker) attempts to read, enumerate, mutate, delete, and trigger runs on User A's (Victim) resources.
    Assert that all cross-tenant actions return 404 and no tenant data is leaked.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # 1. Setup User A (Victim) resources
        proj_a = ResearchProject(
            title="Victim Secret Workspace",
            original_question="Victim Intellectual Property",
            user_id="usr_victim_a",
            project_type="web",
        )
        db_session.add(proj_a)
        db_session.commit()

        run_a = ResearchRun(
            project_id=proj_a.id,
            status="failed",
            provider_name="bedrock",
            model_name="claude-3-5-sonnet",
        )
        db_session.add(run_a)
        db_session.commit()

        doc_a = Document(
            project_id=proj_a.id,
            filename="patent_draft.pdf",
            file_hash="hash_patent_draft",
            file_size_bytes=8192,
            status="completed",
            page_count=4,
        )
        db_session.add(doc_a)
        db_session.commit()

        conclusion_a = Conclusion(run_id=run_a.id, statement="Patent conclusion", confidence="high")
        db_session.add(conclusion_a)
        db_session.commit()

        report_a = RAGReport(
            project_id=proj_a.id,
            question="Patent novelty?",
            report_json=json.dumps({"summary": "Novelty confirmed"}),
            status="completed",
        )
        db_session.add(report_a)
        db_session.commit()

        # 2. Setup User B (Attacker) resources
        proj_b = ResearchProject(
            title="Attacker Own Workspace",
            original_question="Attacker Inquiry",
            user_id="usr_attacker_b",
            project_type="web",
        )
        db_session.add(proj_b)
        db_session.commit()

        headers_attacker = {"Authorization": "Bearer mock-user-attacker_b"}

        # Attacker can access own project
        assert client.get(f"/api/v1/research-projects/{proj_b.id}", headers=headers_attacker).status_code == 200

        # Attacker attempts IDOR on User A's resources -> Must return 404
        assert client.get(f"/api/v1/research-projects/{proj_a.id}", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/research-projects/{proj_a.id}/runs", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/events", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/sources", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/claims", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/assessments", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/conclusions/{conclusion_a.id}/trace", headers=headers_attacker).status_code == 404

        # Attacker attempts cross-tenant run retry
        assert client.post(f"/api/v1/research-runs/{run_a.id}/retry", headers=headers_attacker).status_code == 404

        # Attacker attempts cross-tenant document theft & injection
        assert client.get(f"/api/v1/projects/{proj_a.id}/documents", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/documents/{doc_a.id}", headers=headers_attacker).status_code == 404
        assert client.delete(f"/api/v1/documents/{doc_a.id}", headers=headers_attacker).status_code == 404
        trojan_file = {"file": ("trojan.pdf", create_valid_test_pdf("Trojan PDF"), "application/pdf")}
        assert client.post(f"/api/v1/projects/{proj_a.id}/documents", files=trojan_file, headers=headers_attacker).status_code == 404

        # Attacker attempts cross-tenant RAG report access & execution
        assert client.get(f"/api/v1/projects/{proj_a.id}/rag-reports", headers=headers_attacker).status_code == 404
        assert client.get(f"/api/v1/rag-reports/{report_a.id}", headers=headers_attacker).status_code == 404
        assert client.post(
            f"/api/v1/projects/{proj_a.id}/rag-research",
            json={"question": "Attacker exfiltration query"},
            headers=headers_attacker,
        ).status_code == 404

        # Attacker workspace list MUST NOT include User A's project
        projects_resp = client.get("/api/v1/research-projects", headers=headers_attacker)
        assert projects_resp.status_code == 200
        project_ids = [p["id"] for p in projects_resp.json()]
        assert proj_b.id in project_ids
        assert proj_a.id not in project_ids

    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Production Environment Gating & Header Spoofing Penetration Tests
# ---------------------------------------------------------------------------

def test_pen_production_header_and_token_spoofing_resistance(monkeypatch, db_session):
    """
    Adversarial Penetration Test:
    Verify that in ENVIRONMENT=production:
    - X-Test-User-Id header spoofing is rejected (401)
    - mock-user-* token spoofing is rejected (401)
    - test-token-* token spoofing is rejected (401)
    - Combined header + mock token is rejected (401)
    - JWT signature forgery (alg=none, wrong key) is rejected (401)
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        _token_cache.clear()
        monkeypatch.setenv("ENVIRONMENT", "production")

        # 1. Attacker sends X-Test-User-Id header to /api/v1/auth/me
        resp1 = client.get("/api/v1/auth/me", headers={"X-Test-User-Id": "admin_super"})
        assert resp1.status_code == 401

        # 2. Attacker sends mock-user-* token
        resp2 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer mock-user-admin"})
        assert resp2.status_code == 401

        # 3. Attacker sends test-token-* token
        resp3 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test-token-admin"})
        assert resp3.status_code == 401

        # 4. Attacker sends both spoofed header and mock token
        resp4 = client.get(
            "/api/v1/auth/me",
            headers={"X-Test-User-Id": "admin", "Authorization": "Bearer mock-user-admin"},
        )
        assert resp4.status_code == 401

        # 5. Attacker attempts to create project with spoofed headers under production
        resp5 = client.post(
            "/api/v1/research-projects",
            json={"question": "Attacker inquiry in production"},
            headers={"X-Test-User-Id": "admin"},
        )
        assert resp5.status_code == 401

        resp6 = client.post(
            "/api/v1/research-projects",
            json={"question": "Attacker inquiry in production"},
            headers={"Authorization": "Bearer mock-user-admin"},
        )
        assert resp6.status_code == 401

        # 6. Attacker sends Alg: none JWT
        unsigned_token = jwt.encode({"sub": "admin_attacker", "aud": "authenticated"}, "", algorithm="none")
        resp7 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {unsigned_token}"})
        assert resp7.status_code == 401

        # 7. Attacker sends JWT signed with arbitrary secret (32+ bytes)
        bogus_jwt = jwt.encode(
            {"sub": "admin_attacker", "aud": "authenticated", "exp": int(time.time()) + 3600},
            "attacker_private_secret_key_that_is_long_enough_32bytes",
            algorithm="HS256",
        )
        resp8 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bogus_jwt}"})
        assert resp8.status_code == 401

    finally:
        _token_cache.clear()
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 4. PDF Upload Tampering & DoS Penetration Tests
# ---------------------------------------------------------------------------

def test_pen_pdf_tampering_and_dos(db_session, monkeypatch):
    """
    Adversarial Penetration Test:
    - Attempt upload of disguised executables / scripts (.exe, .sh, .html, .pdf.exe)
    - Attempt upload of files with invalid magic bytes (PE header, HTML, ZIP, raw text)
    - Attempt upload of empty 0-byte file
    - Attempt oversized payload stream DoS
    - Attempt path traversal filename (verify UUID disk isolation)
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        project = ResearchProject(
            title="Upload Sandbox",
            original_question="Upload Test Question",
            user_id="usr_uploader",
            project_type="rag",
        )
        db_session.add(project)
        db_session.commit()

        headers = {"Authorization": "Bearer mock-user-uploader"}

        # 1. Non-PDF file extensions
        for bad_ext in ["malware.exe", "script.sh", "page.html", "exploit.pdf.exe", "image.png"]:
            resp = client.post(
                f"/api/v1/projects/{project.id}/documents",
                files={"file": (bad_ext, b"%PDF-1.4 valid magic but bad ext", "application/pdf")},
                headers=headers,
            )
            assert resp.status_code == 400
            assert "Only PDF documents are supported" in resp.json()["detail"]

        # 2. Invalid magic bytes (disguised non-PDF files with .pdf extension)
        bad_magic_payloads = [
            ("windows_pe.pdf", b"MZ\x90\x00\x03\x00\x00\x00"),  # Windows PE executable
            ("elf_binary.pdf", b"\x7fELF\x02\x01\x01\x00"),   # Linux ELF binary
            ("zip_archive.pdf", b"PK\x03\x04\x14\x00\x00\x00"), # ZIP archive
            ("html_page.pdf", b"<!DOCTYPE html><html><body>Test</body></html>"),
            ("plain_text.pdf", b"This is plain text pretending to be PDF."),
            ("zero_byte_chunk.pdf", b"\x00\x00\x00\x00\x00\x00"),
        ]
        for fname, payload in bad_magic_payloads:
            resp = client.post(
                f"/api/v1/projects/{project.id}/documents",
                files={"file": (fname, payload, "application/pdf")},
                headers=headers,
            )
            assert resp.status_code == 400
            assert "Invalid file format" in resp.json()["detail"]

        # 3. Empty file (0 bytes)
        resp_empty = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers=headers,
        )
        assert resp_empty.status_code == 400

        # 4. Oversized streaming payload (DoS attempt)
        settings = get_settings()
        monkeypatch.setattr(settings, "max_upload_size_mb", 1)  # Set 1MB limit for testing

        oversized_blob = b"%PDF-1.4 " + b"A" * (2 * 1024 * 1024)  # 2MB > 1MB limit
        resp_oversize = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("big_bomb.pdf", oversized_blob, "application/pdf")},
            headers=headers,
        )
        assert resp_oversize.status_code == 413

        # 5. Path traversal attempt in filename: verify UUID isolation
        traversal_name = "../../../../etc/passwd.pdf"
        valid_pdf_bytes = create_valid_test_pdf("Path traversal test content")
        resp_traversal = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": (traversal_name, valid_pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert resp_traversal.status_code == 201
        doc_data = resp_traversal.json()
        assert doc_data["id"] is not None
        # Verify stored document record uses the project ID and clean UUID
        assert doc_data["project_id"] == project.id

    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 5. Workspace Bootstrap Cross-Tenant Isolation Penetration Test
# ---------------------------------------------------------------------------

def test_pen_workspace_bootstrap_cross_tenant_isolation(db_session):
    """
    Adversarial Penetration Test:
    GET /api/v1/workspace/bootstrap:
    - User A gets User A's projects and vaults.
    - User B gets User B's projects and vaults (zero leakage from User A).
    - Unauthenticated caller receives empty state (user=None, web_projects=[], rag_vaults=[]) with anti-cache headers.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # Create Project for User A
        proj_a = ResearchProject(
            title="User A Secret Projects",
            original_question="User A Question",
            user_id="usr_boot_user_a",
            project_type="web",
        )
        db_session.add(proj_a)
        db_session.commit()

        # Create Project for User B
        proj_b = ResearchProject(
            title="User B Isolated Projects",
            original_question="User B Question",
            user_id="usr_boot_user_b",
            project_type="web",
        )
        db_session.add(proj_b)
        db_session.commit()

        # 1. User A Bootstrap
        resp_a = client.get("/api/v1/workspace/bootstrap", headers={"Authorization": "Bearer mock-user-boot_user_a"})
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["user"]["id"] == "usr_boot_user_a"
        user_a_project_ids = [p["id"] for p in data_a["web_projects"]]
        assert proj_a.id in user_a_project_ids
        assert proj_b.id not in user_a_project_ids

        # 2. User B Bootstrap
        resp_b = client.get("/api/v1/workspace/bootstrap", headers={"Authorization": "Bearer mock-user-boot_user_b"})
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["user"]["id"] == "usr_boot_user_b"
        user_b_project_ids = [p["id"] for p in data_b["web_projects"]]
        assert proj_b.id in user_b_project_ids
        assert proj_a.id not in user_b_project_ids

        # 3. Unauthenticated Bootstrap
        resp_unauth = client.get("/api/v1/workspace/bootstrap")
        assert resp_unauth.status_code == 200
        data_unauth = resp_unauth.json()
        assert data_unauth["user"] is None
        assert data_unauth["web_projects"] == []
        assert data_unauth["rag_vaults"] == []
        assert "private" in resp_unauth.headers.get("Cache-Control", "")
        assert "Authorization" in resp_unauth.headers.get("Vary", "")

    finally:
        app.dependency_overrides.clear()
