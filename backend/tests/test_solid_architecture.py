import inspect
import pytest

from app.ai.base import BaseLLMProvider
from app.ai.bedrock import BedrockProvider
from app.ai.factory import get_llm_provider
from app.ai.openai_compatible import OpenAICompatibleProvider
from app.config import Settings
from app.search.tavily import TavilyProvider


def test_srp_single_responsibility():
    """Verify that domain modules maintain strict single responsibilities."""
    # AI provider handles LLM calls, not database persistence
    assert not hasattr(BedrockProvider, "db")
    assert not hasattr(OpenAICompatibleProvider, "db")

    # Search provider handles external web queries, not AI synthesis
    assert not hasattr(TavilyProvider, "synthesise_conclusions")


def test_ocp_open_closed_provider_extensibility():
    """Verify that new AI providers can implement BaseLLMProvider without modifying core service contracts."""
    class CustomEnterpriseLLMProvider(BaseLLMProvider):
        def plan(self, question: str, max_queries: int) -> dict[str, list[str]]:
            return {"queries": [f"Query for {question}"]}

        def extract_claims(self, source_text: str, source_url: str, max_claims: int) -> list[dict[str, str]]:
            return []

        def compare_claims(self, left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
            return {"relationship": "supports", "rationale": "Aligned"}

        def synthesise(self, question: str, claims: list[dict[str, str]], assessments: list[dict[str, str]]) -> list[dict]:
            return []

    custom_provider = CustomEnterpriseLLMProvider()
    assert isinstance(custom_provider, BaseLLMProvider)
    plan = custom_provider.plan("AI in healthcare", 3)
    assert len(plan["queries"]) == 1
    assert "healthcare" in plan["queries"][0]


def test_lsp_liskov_substitution():
    """Verify that BedrockProvider and OpenAICompatibleProvider satisfy all abstract methods of BaseLLMProvider."""
    abstract_methods = inspect.getmembers(BaseLLMProvider, predicate=inspect.isfunction)
    abstract_method_names = {name for name, _ in abstract_methods if getattr(_, "__isabstractmethod__", False)}

    for provider_cls in [BedrockProvider, OpenAICompatibleProvider]:
        for method_name in abstract_method_names:
            method = getattr(provider_cls, method_name, None)
            assert method is not None, f"{provider_cls.__name__} violates LSP: Missing abstract method {method_name}"
            assert callable(method)


def test_dip_dependency_inversion_via_settings():
    """Verify that provider factory decouples service from concrete implementation using configuration abstraction."""
    bedrock_settings = Settings(ai_provider="bedrock")
    openai_settings = Settings(ai_provider="openai_compatible", ai_api_key="mock-key")

    provider_bedrock = get_llm_provider(bedrock_settings)
    assert isinstance(provider_bedrock, BedrockProvider)
    assert isinstance(provider_bedrock, BaseLLMProvider)

    provider_openai = get_llm_provider(openai_settings)
    assert isinstance(provider_openai, OpenAICompatibleProvider)
    assert isinstance(provider_openai, BaseLLMProvider)
