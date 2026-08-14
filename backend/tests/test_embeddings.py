import pytest
from app.config import Settings
from app.embeddings.provider import EmbeddingProvider, EmbeddingProviderError


def test_embedding_provider_initialization():
    settings = Settings(embedding_model_id="cohere.embed-english-v3.0", embedding_dims=1024)
    provider = EmbeddingProvider(settings)
    assert provider.dims == 1024
    assert provider.model_id == "cohere.embed-english-v3.0"


def test_embedding_provider_deterministic_fallback():
    settings = Settings(embedding_model_id="cohere.embed-english-v3.0", embedding_dims=1024)
    provider = EmbeddingProvider(settings)
    
    # Generate embeddings for test sentences
    texts = [
        "Enterprise document research using RAG architecture.",
        "PostgreSQL with pgvector offers high throughput vector search.",
    ]
    embeddings = provider.embed(texts, input_type="search_document")
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1024
    assert len(embeddings[1]) == 1024
    
    # Check normalization (unit length vector: norm ~= 1.0)
    norm = sum(x * x for x in embeddings[0]) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_embedding_provider_single_query():
    settings = Settings(embedding_model_id="cohere.embed-english-v3.0", embedding_dims=1024)
    provider = EmbeddingProvider(settings)
    query_vec = provider.embed_query("What is the Q3 revenue?")
    assert len(query_vec) == 1024


def test_embedding_provider_batching():
    settings = Settings(
        embedding_model_id="cohere.embed-english-v3.0",
        embedding_dims=1024,
        embedding_batch_size=2,
    )
    provider = EmbeddingProvider(settings)
    texts = [f"Sentence number {i} for batching test." for i in range(7)]
    embeddings = provider.embed(texts)
    assert len(embeddings) == 7
    for vec in embeddings:
        assert len(vec) == 1024


def test_embedding_validate_dimensions():
    settings = Settings(embedding_dims=1024)
    provider = EmbeddingProvider(settings)
    # Should not raise
    provider.validate_dimensions()
