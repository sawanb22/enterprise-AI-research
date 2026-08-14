import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.base import BaseLLMProvider
from ..config import Settings, get_settings
from ..embeddings.provider import EmbeddingProvider
from ..models import Document, DocumentChunk
from .schemas import ScoredChunk

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Multi-query semantic retriever using native pgvector HNSW cosine search on PostgreSQL."""

    def __init__(self, settings: Settings | None = None, embedder: EmbeddingProvider | None = None):
        self.settings = settings or get_settings()
        self.embedder = embedder or EmbeddingProvider(self.settings)

    def expand_query(self, query: str, llm: BaseLLMProvider | None = None) -> list[str]:
        """Expand user query into 2-3 search sub-queries to maximize document chunk recall."""
        if not llm:
            return [query]

        prompt = (
            f"Generate 2-3 distinct, specific search queries or keyword phrases to find relevant evidence in enterprise documents for this research question:\n"
            f"Question: {query}\n\n"
            "Output strictly a JSON array of strings, e.g. [\"query 1\", \"query 2\", \"query 3\"]. No other text."
        )

        try:
            messages = [{"role": "user", "content": prompt}]
            if hasattr(llm, "_request_json"):
                data = llm._request_json(messages)
                if isinstance(data, list):
                    queries = [str(q).strip() for q in data if str(q).strip()]
                    if queries:
                        return [query] + queries[:2]
        except Exception as exc:
            logger.debug("Query expansion failed, using original query: %s", exc)

        return [query]

    def _query_pgvector(
        self,
        project_id: str,
        query_vector: list[float],
        db: Session,
        limit: int,
    ) -> list[tuple[DocumentChunk, str, float]]:
        """Query Supabase PostgreSQL using native pgvector cosine_distance operator (<=>)."""
        stmt = (
            select(
                DocumentChunk,
                Document.filename,
                DocumentChunk.embedding.cosine_distance(query_vector).label("distance"),
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                Document.project_id == project_id,
                Document.status == "ready",
            )
            .order_by("distance")
            .limit(limit)
        )
        results = db.execute(stmt).all()
        # Convert distance to similarity score: score = 1.0 - distance
        return [(row[0], row[1], max(0.0, 1.0 - float(row[2]))) for row in results]

    def retrieve_candidates(
        self,
        project_id: str,
        query: str,
        db: Session,
        top_k: int = 50,
        llm: BaseLLMProvider | None = None,
    ) -> list[ScoredChunk]:
        """
        Retrieve top_k semantic chunk candidates across sub-queries using pgvector HNSW search.
        Deduplicates by chunk ID and sorts by highest score.
        """
        queries = self.expand_query(query, llm=llm)
        query_vectors = self.embedder.embed(queries, input_type="search_query")

        seen_chunks: dict[str, ScoredChunk] = {}

        for q_text, q_vec in zip(queries, query_vectors):
            results = self._query_pgvector(project_id, q_vec, db, limit=top_k)

            for chunk, filename, score in results:
                # If chunk already retrieved by a different subquery, keep highest score
                if chunk.id in seen_chunks:
                    if score > seen_chunks[chunk.id].score:
                        seen_chunks[chunk.id].score = score
                else:
                    seen_chunks[chunk.id] = ScoredChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_filename=filename,
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        raw_text=chunk.raw_text,
                        visual_summary=chunk.visual_summary or "",
                        combined_context=chunk.combined_context,
                        token_count=chunk.token_count,
                        score=score,
                    )

        # Sort all unique candidates by score descending
        all_candidates = list(seen_chunks.values())
        all_candidates.sort(key=lambda c: c.score, reverse=True)
        return all_candidates[:top_k]
