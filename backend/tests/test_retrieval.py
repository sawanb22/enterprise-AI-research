import pymupdf

from app.documents.service import DocumentService
from app.models import ResearchProject
from app.rag.retrieval import VectorRetriever


def create_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_vector_retriever_pgvector_search(db_session):
    # 1. Create project and upload 2 distinct documents
    project = ResearchProject(title="AI In Healthcare", original_question="How does AI assist radiology?")
    db_session.add(project)
    db_session.flush()

    service = DocumentService()

    pdf1 = create_pdf("Radiology AI enhances MRI scan anomaly detection with 94% sensitivity.")
    pdf2 = create_pdf("Agricultural drone robotics optimize crop yield and water irrigation.")

    doc1, _ = service.upload_document(project.id, "radiology.pdf", pdf1, db_session)
    doc2, _ = service.upload_document(project.id, "agriculture.pdf", pdf2, db_session)

    service.process_document(doc1.id, db_session)
    service.process_document(doc2.id, db_session)

    # 2. Query retriever using native pgvector
    retriever = VectorRetriever()
    candidates = retriever.retrieve_candidates(
        project_id=project.id,
        query="MRI radiology scans anomaly detection",
        db=db_session,
        top_k=5,
    )

    assert len(candidates) >= 1
    # Ensure most relevant candidate is top
    assert "Radiology AI" in candidates[0].raw_text
    assert candidates[0].document_filename == "radiology.pdf"
