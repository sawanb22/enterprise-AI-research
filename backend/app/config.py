from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    database_url_direct: str | None = None  # Direct connection (port 5432) for Alembic migrations
    ai_provider: str = "bedrock"  # "bedrock" | "openai_compatible"

    # Amazon Bedrock & Mantle Settings
    aws_region: str = "us-east-1"
    aws_bearer_token_bedrock: str | None = None
    aws_bearer_token: str | None = None
    bedrock_api_key: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_endpoint_url: str | None = None

    # Vision AI Model Settings
    vision_model_id: str | None = None

    # Embedding Provider (Amazon Bedrock Cohere)
    embedding_model_id: str = "cohere.embed-english-v3.0"
    embedding_dims: int = 1024
    embedding_batch_size: int = 96

    # Redis & Worker Settings
    redis_url: str = "redis://localhost:6379"

    # Universal OpenAI-Compatible Fallback Settings (MiniMax / Kimi / OpenRouter / Ollama)
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.minimax.chat/v1"
    ai_model: str = "minimax-text-01"

    # Security & API Auth Settings
    api_auth_key: str | None = None
    rate_limit_research_per_min: int = 10
    rate_limit_read_per_min: int = 60

    tavily_api_key: str | None = None
    allowed_origins: str = "http://localhost:5173"
    max_queries: int = 3
    max_sources: int = 6
    max_claims: int = 12
    max_comparisons: int = 10

    # RAG & Ingestion Limits
    max_rag_results: int = 15
    max_rerank_candidates: int = 50
    max_vision_calls_per_doc: int = 20
    max_upload_size_mb: int = 50
    max_pages_per_project: int = 10
    max_pages_per_doc: int = 10
    chunk_target_tokens: int = 800
    chunk_overlap_tokens: int = 200

    @property
    def effective_bedrock_bearer_token(self) -> str | None:
        return (
            self.aws_bearer_token_bedrock
            or self.aws_bearer_token
            or self.bedrock_api_key
            or (self.ai_api_key if self.ai_provider == "bedrock" else None)
        )

    @property
    def effective_provider(self) -> str:
        prov = (self.ai_provider or "").lower().strip()
        if prov in {"openai_compatible", "openai"}:
            return "openai_compatible"
        if prov in {"bedrock", "aws_bedrock"}:
            return "bedrock"
        # Auto-detect if credentials exist
        if self.effective_bedrock_bearer_token or self.aws_access_key_id:
            return "bedrock"
        return "bedrock"

    @property
    def effective_api_key(self) -> str | None:
        return self.ai_api_key

    @property
    def effective_model_name(self) -> str:
        if self.effective_provider == "bedrock":
            return self.bedrock_model_id
        return self.ai_model

    @property
    def effective_vision_model_id(self) -> str:
        return self.vision_model_id or self.effective_model_name

    @property
    def effective_base_url(self) -> str:
        return self.ai_base_url.rstrip("/")

    @property
    def is_ai_configured(self) -> bool:
        if self.effective_provider == "bedrock":
            return bool(self.effective_bedrock_bearer_token or self.aws_access_key_id)
        return bool(self.effective_api_key)

    @property
    def is_embedding_configured(self) -> bool:
        return bool(self.embedding_model_id and self.is_ai_configured)

    @property
    def is_vision_configured(self) -> bool:
        return bool(self.effective_vision_model_id and self.is_ai_configured)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
