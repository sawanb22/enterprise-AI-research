import logging
from typing import Any

from flashrank import Ranker, RerankRequest

from .schemas import ScoredChunk

logger = logging.getLogger(__name__)

_reranker_instance: "FlashRankReranker | None" = None


class FlashRankReranker:
    """High-performance cross-encoder reranker using FlashRank (ONNX)."""

    def __init__(self, model_name: str = "ms-marco-TinyBERT-L-2-v2"):
        self.model_name = model_name
        self.ranker = Ranker(model_name=model_name, cache_dir="/tmp/flashrank")

    def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = 15,
    ) -> list[ScoredChunk]:
        """
        Rerank a list of ScoredChunk candidates using cross-encoder attention against the query.
        Returns top_k chunks sorted by relevance.
        """
        if not candidates:
            return []

        # Prepare passages mapping
        passages = [
            {"id": i, "text": chunk.combined_context}
            for i, chunk in enumerate(candidates)
        ]

        try:
            rerank_request = RerankRequest(query=query, passages=passages)
            results = self.ranker.rerank(rerank_request)

            reranked_chunks: list[ScoredChunk] = []
            for item in results:
                idx = int(item["id"])
                score = float(item["score"])
                original_chunk = candidates[idx]
                
                # Clone chunk with updated rerank score
                updated_chunk = ScoredChunk(
                    chunk_id=original_chunk.chunk_id,
                    document_id=original_chunk.document_id,
                    document_filename=original_chunk.document_filename,
                    page_number=original_chunk.page_number,
                    chunk_index=original_chunk.chunk_index,
                    raw_text=original_chunk.raw_text,
                    visual_summary=original_chunk.visual_summary,
                    combined_context=original_chunk.combined_context,
                    token_count=original_chunk.token_count,
                    score=score,
                )
                reranked_chunks.append(updated_chunk)

            return reranked_chunks[:top_k]

        except Exception as exc:
            logger.warning("FlashRank reranking failed, falling back to vector score order: %s", exc)
            return candidates[:top_k]


def get_reranker() -> FlashRankReranker:
    """Singleton accessor for FlashRank reranker."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = FlashRankReranker()
    return _reranker_instance
