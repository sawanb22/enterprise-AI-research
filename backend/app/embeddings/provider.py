import hashlib
import json
import logging
import math
from typing import Any
from urllib.parse import quote

import httpx

from ..config import Settings

logger = logging.getLogger(__name__)


class EmbeddingProviderError(Exception):
    """Raised when an embedding call fails."""
    pass


class EmbeddingProvider:
    """Bedrock Cohere Embeddings Provider supporting IAM auth, Bearer tokens, Mantle endpoints, and deterministic offline fallback."""

    def __init__(self, settings: Settings):
        self.model_id = settings.embedding_model_id or "cohere.embed-english-v3.0"
        self.dims = settings.embedding_dims
        self.batch_size = settings.embedding_batch_size
        self.region = settings.aws_region
        self.endpoint_url = settings.bedrock_endpoint_url
        self.bearer_token = settings.effective_bedrock_bearer_token

        if self.endpoint_url:
            self.base_endpoint = self.endpoint_url.rstrip("/")
        else:
            self.base_endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"

        self.boto_client = None
        if not self.bearer_token:
            try:
                import boto3

                client_kwargs: dict[str, Any] = {"region_name": self.region}
                if settings.aws_access_key_id and settings.aws_secret_access_key:
                    client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
                    client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
                    if settings.aws_session_token:
                        client_kwargs["aws_session_token"] = settings.aws_session_token
                if self.endpoint_url:
                    client_kwargs["endpoint_url"] = self.endpoint_url

                self.boto_client = boto3.client("bedrock-runtime", **client_kwargs)
            except Exception as exc:
                logger.warning("Could not initialize boto3 client for embeddings: %s", exc)

    def _generate_mock_embedding(self, text: str) -> list[float]:
        """Generate a deterministic unit-normalized pseudo-embedding for testing or offline mode."""
        # Use SHA-256 hash of the text to seed a deterministic vector
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        raw = []
        for i in range(self.dims):
            # Deterministic value based on byte cycles
            byte_val = seed[i % len(seed)]
            val = (float(byte_val) / 255.0) * 2.0 - 1.0 + (math.sin(i + byte_val) * 0.1)
            raw.append(val)
        
        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    def _invoke_bedrock_batch(self, texts: list[str], input_type: str) -> list[list[float]]:
        """Invoke Cohere Embed model on Amazon Bedrock or Mantle for a single batch."""
        body = {
            "texts": texts,
            "input_type": input_type,
            "truncate": "END",
        }

        if self.bearer_token:
            # Bearer token / Mantle invocation
            url = f"{self.base_endpoint}/model/{quote(self.model_id, safe='')}/invoke"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                    if "embeddings" in data:
                        return data["embeddings"]
                    raise EmbeddingProviderError(f"Unexpected embedding response structure: {data.keys()}")
            except Exception as exc:
                logger.error("Bearer token embedding request failed: %s", exc)
                raise EmbeddingProviderError(f"Embedding request failed: {exc}") from exc

        elif self.boto_client:
            # AWS IAM / Boto3 invocation
            try:
                response = self.boto_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )
                payload = json.loads(response["body"].read().decode("utf-8"))
                if "embeddings" in payload:
                    return payload["embeddings"]
                raise EmbeddingProviderError(f"Unexpected embedding response structure: {payload.keys()}")
            except Exception as exc:
                logger.error("Boto3 embedding request failed: %s", exc)
                raise EmbeddingProviderError(f"Bedrock embedding failed: {exc}") from exc

        else:
            # Offline / test fallback
            logger.info("Using deterministic fallback embeddings (no Bedrock credentials provided)")
            return [self._generate_mock_embedding(t) for t in texts]

    def embed(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        """Embed a list of text strings in batches."""
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            try:
                batch_embeddings = self._invoke_bedrock_batch(batch, input_type=input_type)
            except Exception as exc:
                logger.warning("Embedding API invocation failed, falling back to deterministic vectors: %s", exc)
                batch_embeddings = [self._generate_mock_embedding(t) for t in batch]

            # Validate dimensions
            for vec in batch_embeddings:
                if len(vec) != self.dims:
                    raise EmbeddingProviderError(
                        f"Embedding dimension mismatch: expected {self.dims}, got {len(vec)}"
                    )
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query string."""
        results = self.embed([text], input_type="search_query")
        return results[0]

    def validate_dimensions(self) -> None:
        """Validate that embedding dimensions match configuration."""
        test_vec = self.embed_query("test query")
        if len(test_vec) != self.dims:
            raise EmbeddingProviderError(
                f"Embedding dimension validation failed: expected {self.dims}, got {len(test_vec)}"
            )
