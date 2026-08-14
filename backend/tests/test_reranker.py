import pytest
from app.rag.reranker import FlashRankReranker, get_reranker
from app.rag.schemas import ScoredChunk


def test_flashrank_reranker_relevance_ordering():
    reranker = FlashRankReranker()
    
    query = "What is the capital and population of France?"
    
    candidates = [
        ScoredChunk(
            chunk_id="c1",
            document_id="d1",
            document_filename="geography.pdf",
            page_number=1,
            chunk_index=0,
            raw_text="The Eiffel Tower is located in Paris, the capital of France, home to over 2 million residents.",
            visual_summary="",
            combined_context="The Eiffel Tower is located in Paris, the capital of France, home to over 2 million residents.",
            score=0.5,
        ),
        ScoredChunk(
            chunk_id="c2",
            document_id="d2",
            document_filename="astronomy.pdf",
            page_number=3,
            chunk_index=1,
            raw_text="Jupiter is the largest planet in our solar system with 95 known moons.",
            visual_summary="",
            combined_context="Jupiter is the largest planet in our solar system with 95 known moons.",
            score=0.8,  # Higher initial vector score to test reranker reordering
        ),
    ]

    reranked = reranker.rerank(query, candidates, top_k=2)
    assert len(reranked) == 2
    # FlashRank should promote Paris/France passage to top position
    assert reranked[0].chunk_id == "c1"
    assert "Paris" in reranked[0].combined_context


def test_flashrank_singleton():
    r1 = get_reranker()
    r2 = get_reranker()
    assert r1 is r2
