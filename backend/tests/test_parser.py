import pymupdf
import pytest

from app.documents.parser import PDFParser


def create_sample_pdf_bytes() -> bytes:
    """Generate a valid sample PDF in-memory using pymupdf."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Enterprise AI Report 2026\nQuarterly financial summary.\nGrowth reached 45% YoY.", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_parser_text_extraction():
    pdf_bytes = create_sample_pdf_bytes()
    parser = PDFParser(extract_images=False)
    pages = parser.parse_bytes(pdf_bytes)
    
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Enterprise AI Report 2026" in pages[0].text
    assert "Quarterly financial summary." in pages[0].text
    assert "Growth reached 45% YoY." in pages[0].text


def test_pdf_parser_table_to_markdown():
    parser = PDFParser()
    sample_table = [
        ["Quarter", "Revenue ($M)", "Growth"],
        ["Q1", "120", "15%"],
        ["Q2", "150", "25%"],
        ["Q3", "180", "45%"],
    ]
    md = parser._table_to_markdown(sample_table)
    assert "| Quarter | Revenue ($M) | Growth |" in md
    assert "| --- | --- | --- |" in md
    assert "| Q1 | 120 | 15% |" in md
    assert "| Q3 | 180 | 45% |" in md
