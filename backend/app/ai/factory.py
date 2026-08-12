from ..config import Settings
from .base import BaseLLMProvider
from .bedrock import BedrockProvider
from .openai_compatible import OpenAICompatibleProvider


def get_llm_provider(settings: Settings) -> BaseLLMProvider:
    """Factory creating the configured LLM provider (Bedrock or OpenAI-compatible)."""
    if settings.effective_provider == "bedrock":
        return BedrockProvider(settings)
    return OpenAICompatibleProvider(settings)
