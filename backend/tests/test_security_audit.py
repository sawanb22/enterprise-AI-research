import json
import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_verifier import _token_cache
from app.config import get_settings
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
        assert client.get(f"/api/v1/research-projects/{proj_a.id}", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}/events", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}/sources", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/research-runs/{run_a.id}/claims", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/conclusions/{conclusion_a.id}/trace", headers=headers_a).status_code == 200

        # 2. User B attempting to access User A's resources MUST be blocked with 404 (IDOR protection)
        assert client.get(f"/api/v1/research-projects/{proj_a.id}", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-projects/{proj_a.id}/runs", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/events", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/sources", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/claims", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/assessments", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/conclusions/{conclusion_a.id}/trace", headers=headers_b).status_code == 404

    finally:
        app.dependency_overrides.clear()


def test_unauthenticated_access_to_owned_resources_rejected(db_session):
    """Unauthenticated requests targeting owned projects, runs, documents, and RAG reports must return 404 or 401."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # 1. Setup owned web project, run, and artifacts for User A
        proj_a = ResearchProject(
            title="User A Private Project",
            original_question="User A Secret Investigation",
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
        source_a = Source(canonical_url="https://private.corp/doc", title="Private Doc")
        db_session.add_all([event_a, source_a])
        db_session.commit()

        snap_a = SourceSnapshot(source_id=source_a.id, run_id=run_a.id, content_hash="hash_unauth", cleaned_text="Confidential")
        db_session.add(snap_a)
        db_session.commit()

        claim_a = Claim(
            run_id=run_a.id,
            snapshot_id=snap_a.id,
            topic="Private Topic",
            statement="Confidential Statement",
            classification="impact",
            confidence="high",
            exact_excerpt="Confidential",
        )
        db_session.add(claim_a)
        db_session.commit()

        conclusion_a = Conclusion(run_id=run_a.id, statement="Confidential Conclusion", confidence="high")
        db_session.add(conclusion_a)
        db_session.commit()

        link_a = ConclusionClaim(conclusion_id=conclusion_a.id, claim_id=claim_a.id, role="supports")
        db_session.add(link_a)
        db_session.commit()

        # 2. Setup owned document & RAG report for User A
        doc_a = Document(
            project_id=proj_a.id,
            filename="confidential_audit.pdf",
            file_hash="hash_pdf_a",
            file_size_bytes=1024,
            status="completed",
            page_count=2,
        )
        db_session.add(doc_a)
        db_session.commit()

        report_a = RAGReport(
            project_id=proj_a.id,
            question="What is the internal finding?",
            report_json=json.dumps({"summary": "Top secret summary", "sections": []}),
            status="completed",
        )
        db_session.add(report_a)
        db_session.commit()

        # 3. Verify unauthenticated requests (NO headers) to web endpoints return HTTP 404
        assert client.get(f"/api/v1/research-projects/{proj_a.id}").status_code == 404
        assert client.get(f"/api/v1/research-projects/{proj_a.id}/runs").status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}").status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/events").status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/sources").status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/claims").status_code == 404
        assert client.get(f"/api/v1/research-runs/{run_a.id}/assessments").status_code == 404
        assert client.get(f"/api/v1/conclusions/{conclusion_a.id}/trace").status_code == 404

        # 4. Verify unauthenticated retry and mutations return HTTP 401
        assert client.post(f"/api/v1/research-runs/{run_a.id}/retry").status_code == 401
        assert client.post(
            f"/api/v1/projects/{proj_a.id}/rag-research",
            json={"question": "Unauth inquiry"},
        ).status_code == 401

        # 5. Verify unauthenticated document operations return HTTP 404
        assert client.get(f"/api/v1/projects/{proj_a.id}/documents").status_code == 404
        assert client.get(f"/api/v1/documents/{doc_a.id}").status_code == 404
        assert client.delete(f"/api/v1/documents/{doc_a.id}").status_code == 404
        files = {"file": ("upload.pdf", b"%PDF-1.4 test", "application/pdf")}
        assert client.post(f"/api/v1/projects/{proj_a.id}/documents", files=files).status_code == 404

        # 6. Verify unauthenticated RAG report operations return HTTP 404
        assert client.get(f"/api/v1/projects/{proj_a.id}/rag-reports").status_code == 404
        assert client.get(f"/api/v1/rag-reports/{report_a.id}").status_code == 404

    finally:
        app.dependency_overrides.clear()


def test_cross_tenant_document_and_rag_access_rejected(db_session):
    """User B cannot access or modify User A's documents, document details, or RAG reports."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # Create Project, Document, and RAG Report for User A
        proj_a = ResearchProject(
            title="User A Vault",
            original_question="User A Vault Question",
            user_id="usr_user_a",
            project_type="rag",
        )
        db_session.add(proj_a)
        db_session.commit()

        doc_a = Document(
            project_id=proj_a.id,
            filename="user_a_financials.pdf",
            file_hash="hash_fin_a",
            file_size_bytes=2048,
            status="completed",
            page_count=3,
        )
        db_session.add(doc_a)
        db_session.commit()

        report_a = RAGReport(
            project_id=proj_a.id,
            question="What are Q4 revenue numbers?",
            report_json=json.dumps({"summary": "Q4 Revenue: $50M", "sections": []}),
            status="completed",
        )
        db_session.add(report_a)
        db_session.commit()

        headers_a = {"Authorization": "Bearer mock-user-user_a"}
        headers_b = {"Authorization": "Bearer mock-user-user_b"}

        # 1. User A can access own documents and RAG reports
        assert client.get(f"/api/v1/projects/{proj_a.id}/documents", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/documents/{doc_a.id}", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/projects/{proj_a.id}/rag-reports", headers=headers_a).status_code == 200
        assert client.get(f"/api/v1/rag-reports/{report_a.id}", headers=headers_a).status_code == 200

        # 2. User B cannot access User A's documents (must return 404)
        assert client.get(f"/api/v1/projects/{proj_a.id}/documents", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/documents/{doc_a.id}", headers=headers_b).status_code == 404

        # 3. User B cannot upload documents into User A's project (must return 404)
        files = {"file": ("injected.pdf", b"%PDF-1.4 malicious", "application/pdf")}
        upload_resp = client.post(f"/api/v1/projects/{proj_a.id}/documents", files=files, headers=headers_b)
        assert upload_resp.status_code == 404

        # 4. User B cannot delete User A's document (must return 404)
        del_resp = client.delete(f"/api/v1/documents/{doc_a.id}", headers=headers_b)
        assert del_resp.status_code == 404

        # 5. User B cannot trigger RAG research or access RAG reports for User A (must return 404)
        rag_resp = client.post(
            f"/api/v1/projects/{proj_a.id}/rag-research",
            json={"question": "Tampered query"},
            headers=headers_b,
        )
        assert rag_resp.status_code == 404
        assert client.get(f"/api/v1/projects/{proj_a.id}/rag-reports", headers=headers_b).status_code == 404
        assert client.get(f"/api/v1/rag-reports/{report_a.id}", headers=headers_b).status_code == 404

    finally:
        app.dependency_overrides.clear()


def test_environment_gating_test_bypass_headers_and_tokens(monkeypatch, db_session):
    """In production environment, X-Test-User-Id header and mock tokens must be rejected."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # Clear token cache to ensure fresh verification
        _token_cache.clear()

        # 1. Simulate PRODUCTION environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        settings = get_settings()

        # In production: X-Test-User-Id header must NOT authenticate the caller (returns 401)
        resp_test_header = client.get("/api/v1/auth/me", headers={"X-Test-User-Id": "attacker_id"})
        assert resp_test_header.status_code == 401

        # In production: mock-user-* token must NOT authenticate without cryptographic signature (returns 401)
        resp_mock_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer mock-user-attacker"})
        assert resp_mock_token.status_code == 401

        # In production: test-token-* token must NOT authenticate (returns 401)
        resp_test_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test-token-attacker"})
        assert resp_test_token.status_code == 401

        # 2. Simulate DEVELOPMENT / TEST environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        _token_cache.clear()

        # In development: X-Test-User-Id header IS allowed for automated testing
        resp_dev_header = client.get("/api/v1/auth/me", headers={"X-Test-User-Id": "dev_tester"})
        assert resp_dev_header.status_code == 200
        assert resp_dev_header.json()["user"]["id"] == "dev_tester"

        # In development: mock-user-* token IS allowed for local mock testing
        resp_dev_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer mock-user-dev_tester"})
        assert resp_dev_token.status_code == 200
        assert resp_dev_token.json()["user"]["id"] == "usr_dev_tester"

    finally:
        _token_cache.clear()
        app.dependency_overrides.clear()
