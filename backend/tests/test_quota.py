import pymupdf
from fastapi.testclient import TestClient
import pytest

from app.database import get_db
from app.documents import router as doc_router
from app.main import app
from app.models import ResearchProject


def create_pdf_with_pages(page_count: int, sample_text: str = "Test document content") -> bytes:
    """Generate in-memory synthetic PDF with an exact number of pages."""
    doc = pymupdf.open()
    for page_idx in range(page_count):
        page = doc.new_page()
        page.insert_text((50, 50), f"{sample_text} - Page {page_idx + 1}", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_single_doc_over_10_pages_rejected(db_session, monkeypatch):
    monkeypatch.setattr(doc_router, "process_document_background", lambda doc_id: None)
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        project = ResearchProject(title="Large Doc Project", original_question="Testing single doc limit")
        db_session.add(project)
        db_session.commit()

        # Create a 12-page PDF (pilot limit is 10)
        twelve_page_pdf = create_pdf_with_pages(12, "Large Report")
        files = {"file": ("oversized_report.pdf", twelve_page_pdf, "application/pdf")}

        resp = client.post(f"/api/v1/projects/{project.id}/documents", files=files)
        assert resp.status_code == 400
        assert "cannot exceed 10 pages" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_cumulative_project_pages_rejected(db_session, monkeypatch):
    monkeypatch.setattr(doc_router, "process_document_background", lambda doc_id: None)
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        project = ResearchProject(title="Cumulative Quota Project", original_question="Testing cumulative limit")
        db_session.add(project)
        db_session.commit()

        # 1. Upload first 6-page document (6/10 pages -> Allowed)
        doc1_pdf = create_pdf_with_pages(6, "Doc One")
        resp1 = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("doc_one.pdf", doc1_pdf, "application/pdf")},
        )
        assert resp1.status_code == 201
        assert resp1.json()["page_count"] == 6

        # 2. Upload second 6-page document (6 + 6 = 12/10 pages -> Rejected)
        doc2_pdf = create_pdf_with_pages(6, "Doc Two")
        resp2 = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("doc_two.pdf", doc2_pdf, "application/pdf")},
        )
        assert resp2.status_code == 400
        assert "Pilot project quota exceeded" in resp2.json()["detail"]
        assert "6/10 pages" in resp2.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_quota_reclaimed_on_delete_and_listing_metadata(db_session, monkeypatch):
    monkeypatch.setattr(doc_router, "process_document_background", lambda doc_id: None)
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        project = ResearchProject(title="Quota Reclamation Project", original_question="Testing delete quota reclamation")
        db_session.add(project)
        db_session.commit()

        # 1. Upload 7-page document
        doc_pdf = create_pdf_with_pages(7, "Original Doc")
        resp1 = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("original.pdf", doc_pdf, "application/pdf")},
        )
        assert resp1.status_code == 201
        doc_id = resp1.json()["id"]

        # 2. Verify listing quota telemetry
        list_resp = client.get(f"/api/v1/projects/{project.id}/documents")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total"] == 1
        assert data["total_pages"] == 7
        assert data["max_pages_limit"] == 10
        assert data["remaining_pages"] == 3

        # 3. Delete document
        del_resp = client.delete(f"/api/v1/documents/{doc_id}")
        assert del_resp.status_code == 200

        # 4. Verify quota is reclaimed
        list_resp_after = client.get(f"/api/v1/projects/{project.id}/documents")
        data_after = list_resp_after.json()
        assert data_after["total"] == 0
        assert data_after["total_pages"] == 0
        assert data_after["remaining_pages"] == 10

        # 5. Upload new 8-page document (now fits within 10 pages)
        new_doc_pdf = create_pdf_with_pages(8, "New Doc")
        resp2 = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("new_doc.pdf", new_doc_pdf, "application/pdf")},
        )
        assert resp2.status_code == 201
        assert resp2.json()["page_count"] == 8
    finally:
        app.dependency_overrides.clear()
