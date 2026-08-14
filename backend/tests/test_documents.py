import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import get_db
from app.documents.service import DocumentService
from app.main import app
from app.models import Document, DocumentChunk, ResearchProject


def create_test_pdf_bytes(title: str = "Test PDF Document") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"{title}\nThis document contains valuable enterprise data.\nNet profit is up 28%.", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_document_upload_and_deduplication(db_session):
    # 1. Create project
    project = ResearchProject(title="Enterprise AI", original_question="How does AI impact ERP?")
    db_session.add(project)
    db_session.flush()

    service = DocumentService()
    pdf_bytes = create_test_pdf_bytes("Financial Report Q3")

    # 2. First upload
    doc1, is_existing1 = service.upload_document(
        project_id=project.id,
        filename="report.pdf",
        file_bytes=pdf_bytes,
        db=db_session,
    )
    assert doc1.id is not None
    assert doc1.status == "pending"
    assert is_existing1 is False

    # 3. Duplicate upload of same content
    doc2, is_existing2 = service.upload_document(
        project_id=project.id,
        filename="report_copy.pdf",
        file_bytes=pdf_bytes,
        db=db_session,
    )
    assert doc2.id == doc1.id
    assert is_existing2 is True


def test_document_processing_pipeline(db_session):
    # 1. Create project & upload doc
    project = ResearchProject(title="Supply Chain AI", original_question="What are logistics trends?")
    db_session.add(project)
    db_session.flush()

    service = DocumentService()
    pdf_bytes = create_test_pdf_bytes("Logistics Overview")
    doc, _ = service.upload_document(
        project_id=project.id,
        filename="logistics.pdf",
        file_bytes=pdf_bytes,
        db=db_session,
    )

    # 2. Process document
    processed_doc = service.process_document(doc.id, db=db_session)
    assert processed_doc.status == "ready"
    assert processed_doc.page_count == 1
    assert processed_doc.completed_at is not None

    # 3. Verify chunks stored in DB
    chunks = list(
        db_session.scalars(
            select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
        ).all()
    )
    assert len(chunks) >= 1
    assert chunks[0].page_number == 1
    assert "Logistics Overview" in chunks[0].raw_text
    assert chunks[0].embedding is not None


def test_document_api_endpoints(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # 1. Create project
        project = ResearchProject(title="API Test Project", original_question="API Question?")
        db_session.add(project)
        db_session.flush()

        pdf_bytes = create_test_pdf_bytes("API Endpoint PDF")

        # 2. Upload via POST /api/v1/projects/{project_id}/documents
        response = client.post(
            f"/api/v1/projects/{project.id}/documents",
            files={"file": ("api_doc.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 201
        doc_data = response.json()
        doc_id = doc_data["id"]
        assert doc_data["filename"] == "api_doc.pdf"

        # 3. List via GET /api/v1/projects/{project_id}/documents
        list_resp = client.get(f"/api/v1/projects/{project.id}/documents")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # 4. Details via GET /api/v1/documents/{doc_id}
        detail_resp = client.get(f"/api/v1/documents/{doc_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == doc_id

        # 5. Delete via DELETE /api/v1/documents/{doc_id}
        del_resp = client.delete(f"/api/v1/documents/{doc_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True

        # 6. Verify 404 after deletion
        get_after = client.get(f"/api/v1/documents/{doc_id}")
        assert get_after.status_code == 404

    finally:
        app.dependency_overrides.clear()
