from app.models import Document, DocumentChunk, RAGReport, RAGReportCitation, ResearchProject
from app.rag.schemas import ScoredChunk
from app.rag.synthesis import RAGSynthesizer, is_quote_in_text


class MockLLMProvider:
    def __init__(self, response_payload: dict):
        self.payload = response_payload

    def _request_json(self, messages: list[dict]) -> dict:
        return self.payload


def test_quote_normalization_and_matching():
    source_text = 'According to the report, "AI deployment reduced inventory errors by 34% annually."'
    valid_quote = "AI deployment reduced inventory errors by 34% annually."
    invalid_quote = "AI deployment reduced inventory errors by 80%."

    assert is_quote_in_text(valid_quote, source_text) is True
    assert is_quote_in_text(invalid_quote, source_text) is False


def test_rag_synthesizer_verbatim_citation_verification(db_session):
    project = ResearchProject(title="Retail AI", original_question="How does AI cut inventory errors?")
    db_session.add(project)
    db_session.commit()

    doc = Document(
        project_id=project.id,
        filename="retail_study.pdf",
        file_hash="mock_hash_123",
        file_size_bytes=1024,
        status="ready",
        page_count=10,
    )
    db_session.add(doc)
    db_session.commit()

    text_content = "Field studies demonstrated that AI-driven inventory tracking reduced stockouts by 42%."
    chunk_record = DocumentChunk(
        document_id=doc.id,
        page_number=4,
        chunk_index=0,
        raw_text=text_content,
        combined_context=text_content,
        token_count=16,
    )
    db_session.add(chunk_record)
    db_session.commit()

    chunk1 = ScoredChunk(
        chunk_id=chunk_record.id,
        document_id=doc.id,
        document_filename="retail_study.pdf",
        page_number=4,
        chunk_index=0,
        raw_text=chunk_record.raw_text,
        visual_summary="",
        combined_context=chunk_record.combined_context,
        score=0.92,
    )

    mock_llm_response = {
        "summary": "AI systems significantly reduce retail stockouts.",
        "sections": [
            {
                "heading": "Stockout Reductions",
                "content": "Inventory tracking powered by AI achieved a 42% stockout drop.",
                "confidence": "high",
                "citations": [
                    {
                        "source_id": 1,
                        "verbatim_quote": "AI-driven inventory tracking reduced stockouts by 42%",
                    },
                    {
                        "source_id": 1,
                        "verbatim_quote": "Hallucinated quote that never exists in text",
                    },
                ],
            }
        ],
        "limitations": "Findings based on North American retail stores.",
    }

    mock_llm = MockLLMProvider(mock_llm_response)
    synthesizer = RAGSynthesizer(mock_llm)

    report_out = synthesizer.synthesize(
        question="How does AI cut inventory errors?",
        ranked_chunks=[chunk1],
        project_id=project.id,
        db=db_session,
    )

    assert report_out.id is not None
    assert report_out.summary == "AI systems significantly reduce retail stockouts."
    assert len(report_out.sections) == 1

    # Check that valid quote passed and hallucinated quote was rejected
    sec = report_out.sections[0]
    assert len(sec.citations) == 1
    assert sec.citations[0].verbatim_quote == "AI-driven inventory tracking reduced stockouts by 42%"
    assert sec.citations[0].document_filename == "retail_study.pdf"
    assert sec.citations[0].page_number == 4

    # Verify DB persistence
    persisted = db_session.get(RAGReport, report_out.id)
    assert persisted is not None
    citations = list(db_session.query(RAGReportCitation).filter_by(report_id=report_out.id).all())
    assert len(citations) == 1
