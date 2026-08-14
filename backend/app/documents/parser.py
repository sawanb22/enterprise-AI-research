from dataclasses import dataclass, field
import io
import logging
from typing import BinaryIO

import pymupdf

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    tables_markdown: list[str] = field(default_factory=list)
    images: list[bytes] = field(default_factory=list)
    has_visuals: bool = False

    @property
    def full_extracted_text(self) -> str:
        """Combine raw text and markdown tables into a unified page string."""
        parts = []
        if self.text.strip():
            parts.append(self.text.strip())
        if self.tables_markdown:
            parts.append("\n\n### Extracted Tables:\n" + "\n\n".join(self.tables_markdown))
        return "\n\n".join(parts)


class PDFParser:
    """High-fidelity PDF document parser using PyMuPDF with structured table and visual extraction."""

    def __init__(self, extract_images: bool = True, max_images_per_page: int = 3):
        self.extract_images = extract_images
        self.max_images_per_page = max_images_per_page

    def _table_to_markdown(self, table_data: list[list[str | None]]) -> str:
        """Convert 2D table grid data to standard Markdown table format."""
        if not table_data or len(table_data) < 1:
            return ""

        # Normalize cells
        cleaned_rows = []
        for row in table_data:
            cleaned_row = [str(cell or "").strip().replace("\n", " ").replace("|", "\\|") for cell in row]
            cleaned_rows.append(cleaned_row)

        if not cleaned_rows:
            return ""

        headers = cleaned_rows[0]
        # Ensure at least non-empty headers
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        body_lines = []
        for row in cleaned_rows[1:]:
            # Pad row if columns mismatch
            if len(row) < len(headers):
                row.extend([""] * (len(headers) - len(row)))
            body_lines.append("| " + " | ".join(row[: len(headers)]) + " |")

        return "\n".join([header_line, sep_line] + body_lines)

    def parse_document(self, doc: pymupdf.Document) -> list[PageContent]:
        """Parse an opened PyMuPDF Document into a list of PageContent objects."""
        pages: list[PageContent] = []

        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1

                # 1. Extract plain text
                raw_text = page.get_text("text").strip()

                # 2. Extract structured tables via PyMuPDF native table engine
                tables_md: list[str] = []
                try:
                    tables = page.find_tables()
                    for tab in tables:
                        table_data = tab.extract()
                        if table_data:
                            md = self._table_to_markdown(table_data)
                            if md:
                                tables_md.append(md)
                except Exception as exc:
                    logger.debug("Table detection error on page %d: %s", page_num, exc)

                # 3. Detect and extract visual diagrams / images
                page_images: list[bytes] = []
                has_visuals = False

                if self.extract_images:
                    try:
                        image_list = page.get_images(full=True)
                        if image_list:
                            has_visuals = True
                            for img_idx, img_info in enumerate(image_list[: self.max_images_per_page]):
                                xref = img_info[0]
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image.get("image")
                                if image_bytes and len(image_bytes) > 2048:  # Filter tiny icons/spacers
                                    page_images.append(image_bytes)
                    except Exception as exc:
                        logger.debug("Image extraction error on page %d: %s", page_num, exc)

                pages.append(
                    PageContent(
                        page_number=page_num,
                        text=raw_text,
                        tables_markdown=tables_md,
                        images=page_images,
                        has_visuals=has_visuals or bool(tables_md),
                    )
                )
        finally:
            doc.close()

        return pages

    def parse_file(self, file_path: str) -> list[PageContent]:
        """Parse a PDF file from a local filesystem path."""
        doc = pymupdf.open(file_path)
        return self.parse_document(doc)

    def parse_bytes(self, file_bytes: bytes) -> list[PageContent]:
        """Parse a PDF file from in-memory bytes."""
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        return self.parse_document(doc)
