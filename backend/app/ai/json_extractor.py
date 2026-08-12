import json
import re
from typing import Any
from .contracts import ProviderError


def extract_json_payload(raw_content: str) -> dict[str, Any]:
    """Robust extractor that handles <think>...</think> tags, markdown code blocks, and extra prose."""
    if not isinstance(raw_content, str):
        raise ProviderError("Raw content must be a string.")
    cleaned = raw_content.strip()

    # 1. Strip reasoning blocks like <think>...</think> produced by DeepSeek, MiniMax, Kimi, etc.
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", cleaned).strip()

    # 2. Extract from markdown code fences if present
    if "```json" in cleaned:
        parts = cleaned.split("```json")
        if len(parts) > 1:
            cleaned = parts[1].split("```")[0].strip()
    elif "```" in cleaned:
        parts = cleaned.split("```")
        if len(parts) > 1:
            cleaned = parts[1].split("```")[0].strip()

    # 3. Extract between the outermost '{' and '}'
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ProviderError("Parsed JSON was not a dictionary object.")
        return parsed
    except json.JSONDecodeError as exc:
        snippet = (raw_content[:200] + "...") if len(raw_content) > 200 else raw_content
        raise ProviderError(f"Could not parse valid JSON from model response: {snippet}") from exc
