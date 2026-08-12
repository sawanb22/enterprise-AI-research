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
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    tavily_api_key: str | None = None
    allowed_origins: str = "http://localhost:5173"
    max_queries: int = 3
    max_sources: int = 6
    max_claims: int = 12
    max_comparisons: int = 10

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
