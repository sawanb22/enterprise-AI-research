import pymupdf
from fastapi.testclient import TestClient

from app.database import get_db
from app.documents.service import DocumentService
from app.main import app
from app.models import ResearchProject


def create_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_rag_api_flow(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    try:
        # 1. Create project
        project = ResearchProject(title="Semiconductor AI", original_question="What is EUV lithography?")
        db_session.add(project)
        db_session.flush()

        # 2. Upload and process a document
        service = DocumentService()
        pdf_content = create_pdf(
            "Extreme Ultraviolet (EUV) lithography operates at 13.5nm wavelength, enabling sub-3nm chip fabrication nodes."
        )
        doc, _ = service.upload_document(project.id, "euv_tech.pdf", pdf_content, db_session)
        service.process_document(doc.id, db_session)

        # 3. Call RAG Research endpoint
        resp = client.post(
            f"/api/v1/projects/{project.id}/rag-research",
            json={"question": "What is the wavelength used in EUV lithography?"},
        )
        assert resp.status_code == 200
        report_data = resp.json()
        assert report_data["id"] is not None
        assert report_data["question"] == "What is the wavelength used in EUV lithography?"
        assert "summary" in report_data
        assert "sections" in report_data
        report_id = report_data["id"]

        # 4. List reports for project
        list_resp = client.get(f"/api/v1/projects/{project.id}/rag-reports")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # 5. Get report details
        get_resp = client.get(f"/api/v1/rag-reports/{report_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == report_id

    finally:
        app.dependency_overrides.clear()
