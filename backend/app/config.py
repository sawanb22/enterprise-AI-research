from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/research_agent.db"
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

    # Universal OpenAI-Compatible Fallback Settings (MiniMax / Kimi / OpenRouter / Ollama)
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.minimax.chat/v1"
    ai_model: str = "minimax-text-01"

    tavily_api_key: str | None = None
    allowed_origins: str = "http://localhost:5173"
    max_queries: int = 3
    max_sources: int = 6
    max_claims: int = 12
    max_comparisons: int = 10

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
    def effective_base_url(self) -> str:
        return self.ai_base_url.rstrip("/")

    @property
    def is_ai_configured(self) -> bool:
        if self.effective_provider == "bedrock":
            return bool(self.effective_bedrock_bearer_token or self.aws_access_key_id or self.aws_region)
        return bool(self.effective_api_key)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
