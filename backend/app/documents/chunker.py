from dataclasses import dataclass
import re

from .parser import PageContent


@dataclass
class ChunkData:
    page_number: int
    chunk_index: int
    raw_text: str
    visual_summary: str
    combined_context: str
    token_count: int


class SmartChunker:
    """Token-aware semantic chunker that respects paragraph and sentence boundaries with context overlap."""

    def __init__(self, target_tokens: int = 800, overlap_tokens: int = 200):
        self.target_tokens = max(100, target_tokens)
        self.overlap_tokens = min(overlap_tokens, self.target_tokens // 2)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count based on whitespace and punctuation words (approx 4 chars/token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _split_into_units(self, text: str) -> list[str]:
        """Split text into semantic units (paragraphs, lists, then sentences if necessary)."""
        # Split by double newlines first (paragraphs / markdown blocks)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        units: list[str] = []

        for p in paragraphs:
            if self._estimate_tokens(p) <= self.target_tokens:
                units.append(p)
            else:
                # Split large paragraphs into sentences
                sentences = re.split(r"(?<=[.!?])\s+", p)
                for s in sentences:
                    if s.strip():
                        units.append(s.strip())
        return units

    def chunk_page(self, page: PageContent, visual_summary: str = "") -> list[ChunkData]:
        """Split a single PageContent into one or more ChunkData objects."""
        page_text = page.full_extracted_text
        page_tokens = self._estimate_tokens(page_text)

        # If page fits in a single chunk, return immediately
        if page_tokens <= self.target_tokens:
            combined = page_text
            if visual_summary.strip():
                combined = f"{page_text}\n\n[Visual / Chart Analysis]:\n{visual_summary.strip()}"
            return [
                ChunkData(
                    page_number=page.page_number,
                    chunk_index=0,
                    raw_text=page_text,
                    visual_summary=visual_summary.strip(),
                    combined_context=combined,
                    token_count=page_tokens,
                )
            ]

        # Multi-chunk sliding window splitting
        units = self._split_into_units(page_text)
        chunks: list[ChunkData] = []
        current_units: list[str] = []
        current_tokens = 0
        chunk_idx = 0

        for unit in units:
            unit_tokens = self._estimate_tokens(unit)
            if current_tokens + unit_tokens > self.target_tokens and current_units:
                # Flush current chunk
                raw_chunk = "\n\n".join(current_units)
                combined = raw_chunk
                if visual_summary.strip():
                    combined = f"{raw_chunk}\n\n[Visual / Chart Analysis]:\n{visual_summary.strip()}"

                chunks.append(
                    ChunkData(
                        page_number=page.page_number,
                        chunk_index=chunk_idx,
                        raw_text=raw_chunk,
                        visual_summary=visual_summary.strip(),
                        combined_context=combined,
                        token_count=current_tokens,
                    )
                )
                chunk_idx += 1

                # Keep overlap units
                overlap_units: list[str] = []
                overlap_tok = 0
                for u in reversed(current_units):
                    u_tok = self._estimate_tokens(u)
                    if overlap_tok + u_tok <= self.overlap_tokens:
                        overlap_units.insert(0, u)
                        overlap_tok += u_tok
                    else:
                        break
                current_units = overlap_units + [unit]
                current_tokens = sum(self._estimate_tokens(u) for u in current_units)
            else:
                current_units.append(unit)
                current_tokens += unit_tokens

        # Flush trailing chunk
        if current_units:
            raw_chunk = "\n\n".join(current_units)
            combined = raw_chunk
            if visual_summary.strip():
                combined = f"{raw_chunk}\n\n[Visual / Chart Analysis]:\n{visual_summary.strip()}"

            chunks.append(
                ChunkData(
                    page_number=page.page_number,
                    chunk_index=chunk_idx,
                    raw_text=raw_chunk,
                    visual_summary=visual_summary.strip(),
                    combined_context=combined,
                    token_count=current_tokens,
                )
            )

        return chunks

    def chunk_pages(
        self, pages: list[PageContent], visual_summaries: dict[int, str] | None = None
    ) -> list[ChunkData]:
        """Chunk a sequence of pages."""
        visuals = visual_summaries or {}
        all_chunks: list[ChunkData] = []

        for page in pages:
            summary = visuals.get(page.page_number, "")
            page_chunks = self.chunk_page(page, visual_summary=summary)
            all_chunks.extend(page_chunks)

        return all_chunks
