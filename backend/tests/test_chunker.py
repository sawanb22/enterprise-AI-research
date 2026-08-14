import pytest
from app.documents.chunker import SmartChunker
from app.documents.parser import PageContent


def test_smart_chunker_short_text_single_chunk():
    chunker = SmartChunker(target_tokens=800, overlap_tokens=200)
    page = PageContent(
        page_number=1,
        text="This is a short paragraph that fits easily within a single 800 token chunk.",
    )
    chunks = chunker.chunk_page(page)
    assert len(chunks) == 1
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert "This is a short paragraph" in chunks[0].raw_text
    assert chunks[0].token_count > 0


def test_smart_chunker_with_visual_summary():
    chunker = SmartChunker(target_tokens=800, overlap_tokens=200)
    page = PageContent(
        page_number=2,
        text="Page text describing quarterly sales distribution across North America.",
    )
    visual_summary = "Bar chart showing Q3 revenue: NA=$40M, EU=$30M, APAC=$20M."
    chunks = chunker.chunk_page(page, visual_summary=visual_summary)
    
    assert len(chunks) == 1
    assert chunks[0].visual_summary == visual_summary
    assert "[Visual / Chart Analysis]:" in chunks[0].combined_context
    assert "NA=$40M" in chunks[0].combined_context


def test_smart_chunker_long_text_multi_chunks():
    chunker = SmartChunker(target_tokens=50, overlap_tokens=15)
    long_text = "\n\n".join([f"Paragraph {i}: " + "Detailed enterprise analysis. " * 5 for i in range(10)])
    page = PageContent(page_number=1, text=long_text)
    
    chunks = chunker.chunk_page(page)
    assert len(chunks) > 1
    assert all(c.page_number == 1 for c in chunks)
    # Ensure sequential chunk indexes
    indexes = [c.chunk_index for c in chunks]
    assert indexes == list(range(len(chunks)))
