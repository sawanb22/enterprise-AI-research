from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    def plan(self, question: str, max_queries: int) -> dict[str, list[str]]:
        pass

    @abstractmethod
    def extract_claims(self, source_text: str, source_url: str, max_claims: int) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def compare_claims(self, left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
        pass

    @abstractmethod
    def synthesise(self, question: str, claims: list[dict[str, str]], assessments: list[dict[str, str]]) -> list[dict[str, Any]]:
        pass
