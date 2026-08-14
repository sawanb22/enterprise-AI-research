import json
import pytest

from app.config import Settings
from app.ai import (
    BedrockProvider,
    OpenAICompatibleProvider,
    extract_json_payload,
    get_llm_provider,
)


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.text = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            request = httpx.Request("POST", "https://api.test.com")
            response = httpx.Response(self.status_code, request=request, text=self.text)
            raise httpx.HTTPStatusError("Error", request=request, response=response)
        return None

    def json(self):
        return {
            "choices": [{"message": {"content": self.content}}],
            "output": {"message": {"content": [{"text": self.content}]}},
        }


def test_extract_json_payload_with_think_tags():
    raw = (
        "<think>Let me reason about the research question step by step...\n"
        "The user wants 2 queries.</think>\n"
        "```json\n"
        '{"sub_questions": ["What is happening?"], "search_queries": ["retail AI impact"]}\n'
        "```"
    )
    result = extract_json_payload(raw)
    assert result == {"sub_questions": ["What is happening?"], "search_queries": ["retail AI impact"]}


def test_extract_json_payload_with_prose_and_fences():
    raw = 'Here is your structured answer:\n{"statement": "AI improves inventory forecasting", "confidence": "high"}\nHope this helps!'
    result = extract_json_payload(raw)
    assert result["confidence"] == "high"
    assert "statement" in result


def test_plan_repairs_one_invalid_structured_response(monkeypatch):
    responses = iter(
        [
            FakeResponse(json.dumps({"unexpected": "shape"})),
            FakeResponse(json.dumps({"sub_questions": ["What changes?"], "search_queries": ["AI retail operations research"]})),
        ]
    )
    monkeypatch.setattr("app.ai.openai_compatible.httpx.post", lambda *args, **kwargs: next(responses))
    provider = OpenAICompatibleProvider(Settings(ai_api_key="test-key"))
    plan = provider.plan("How is AI transforming retail operations?", 1)
    assert plan["search_queries"] == ["AI retail operations research"]
    assert provider.repair_count == 1


def test_openai_compatible_custom_base_url(monkeypatch):
    captured_urls = []

    def mock_post(url, *args, **kwargs):
        captured_urls.append(url)
        return FakeResponse(
            '{"sub_questions": ["Q1"], "search_queries": ["Query 1"]}'
        )

    monkeypatch.setattr("app.ai.openai_compatible.httpx.post", mock_post)
    settings = Settings(
        ai_provider="openai_compatible",
        ai_base_url="https://api.minimax.chat/v1",
        ai_api_key="minimax-secret",
        ai_model="minimax-text-01",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, OpenAICompatibleProvider)
    plan = provider.plan("Test question?", 2)
    assert plan["search_queries"] == ["Query 1"]
    assert "https://api.minimax.chat/v1/chat/completions" in captured_urls


def test_bedrock_bearer_token_converse_request(monkeypatch):
    captured = {}

    def mock_post(url, headers, json, timeout):
        captured["url"] = url
        captured["auth"] = headers.get("Authorization")
        captured["payload"] = json
        return FakeResponse(
            '{"sub_questions": ["Bedrock Q1"], "search_queries": ["Bedrock query 1"]}'
        )

    monkeypatch.setattr("app.ai.bedrock.httpx.post", mock_post)
    settings = Settings(
        ai_provider="bedrock",
        aws_bearer_token_bedrock="ABSK_TEST_TOKEN",
        aws_region="us-east-1",
        bedrock_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, BedrockProvider)
    plan = provider.plan("How does Bedrock work?", 2)
    assert plan["sub_questions"] == ["Bedrock Q1"]
    assert captured["auth"] == "Bearer ABSK_TEST_TOKEN"
    assert "bedrock-mantle.us-east-1.api.aws" in captured["url"]


def test_synthesise_includes_reasoning(monkeypatch):
    synthesis_payload = {
        "conclusions": [
            {
                "statement": "Demand forecasting error dropped by 30%.",
                "confidence": "high",
                "claim_ids": ["claim-1", "claim-2"],
                "reasoning": "Both source A and source B corroborated 30% error reduction in pilot studies with strong statistical power.",
                "limitations": "Only applies to apparel sector.",
            }
        ]
    }

    def mock_post(*args, **kwargs):
        return FakeResponse(json.dumps(synthesis_payload))

    monkeypatch.setattr("app.ai.openai_compatible.httpx.post", mock_post)
    provider = OpenAICompatibleProvider(Settings(ai_api_key="test-key"))
    conclusions = provider.synthesise("What is the impact?", [{"id": "claim-1"}], [])
    assert len(conclusions) == 1
    assert "Both source A and source B corroborated" in conclusions[0]["reasoning"]
    assert conclusions[0]["confidence"] == "high"


def test_get_llm_provider_factory():
    # Auto-detection when Bedrock bearer token is provided
    bedrock_token_settings = Settings(aws_bearer_token_bedrock="ABSK_123")
    provider = get_llm_provider(bedrock_token_settings)
    assert isinstance(provider, BedrockProvider)

    # Explicit OpenAI-compatible selection
    openai_settings = Settings(ai_provider="openai_compatible", ai_api_key="test-key")
    openai_provider = get_llm_provider(openai_settings)
    assert isinstance(openai_provider, OpenAICompatibleProvider)


def test_bedrock_repair_alternates_roles_correctly(monkeypatch):
    recorded_requests = []

    def mock_post(url, headers, json, timeout):
        recorded_requests.append({"url": url, "payload": json})
        if len(recorded_requests) == 1:
            # First response returns invalid schema
            return FakeResponse('{"unexpected": "format"}')
        # Repair response returns valid schema
        return FakeResponse('{"sub_questions": ["Sub Q1"], "search_queries": ["Bedrock query 1"]}')

    monkeypatch.setattr("app.ai.bedrock.httpx.post", mock_post)
    provider = BedrockProvider(Settings(aws_bearer_token_bedrock="TEST_TOKEN", aws_region="us-east-1"))
    plan = provider.plan("Test question?", 1)
    assert plan["sub_questions"] == ["Sub Q1"]
    assert provider.repair_count == 1
    assert len(recorded_requests) == 2

    repair_messages = recorded_requests[1]["payload"]["messages"]
    # Check that roles alternate user -> assistant -> user (or system -> user -> assistant -> user)
    non_system_roles = [m["role"] for m in repair_messages if m["role"] != "system"]
    assert non_system_roles == ["user", "assistant", "user"]


def test_openai_compatible_recovers_on_422_response_format(monkeypatch):
    calls = []

    def mock_post(url, headers, json, timeout):
        calls.append(json)
        if "response_format" in json:
            return FakeResponse('{"error": "Unsupported parameter: response_format"}', status_code=422)
        return FakeResponse('{"sub_questions": ["Q1"], "search_queries": ["Query 1"]}')

    monkeypatch.setattr("app.ai.openai_compatible.httpx.post", mock_post)
    provider = OpenAICompatibleProvider(Settings(ai_api_key="test-key"))
    plan = provider.plan("Test question?", 1)
    assert plan["search_queries"] == ["Query 1"]
    assert len(calls) == 2
    assert "response_format" in calls[0]
    assert "response_format" not in calls[1]


def test_is_ai_configured_requires_actual_credentials():
    # Only default aws_region="us-east-1", no keys
    settings_no_creds = Settings(
        ai_provider="bedrock",
        aws_region="us-east-1",
        aws_access_key_id=None,
        aws_bearer_token_bedrock=None,
        ai_api_key=None,
    )
    assert settings_no_creds.is_ai_configured is False

    # With Bearer token
    settings_bearer = Settings(
        ai_provider="bedrock",
        aws_bearer_token_bedrock="ABSK_VALID",
        aws_access_key_id=None,
    )
    assert settings_bearer.is_ai_configured is True

    # With IAM access key
    settings_iam = Settings(
        ai_provider="bedrock",
        aws_access_key_id="AKIA_VALID",
        aws_bearer_token_bedrock=None,
    )
    assert settings_iam.is_ai_configured is True


def test_tavily_extract_uses_content_fallback(monkeypatch):
    from app.search.tavily import TavilyProvider

    class FakeTavilyResponse:
        def __init__(self, data):
            self._data = data
            self.status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    # raw_content is None, but content is provided
    sample_text = "This is a detailed analysis of enterprise AI adoption across global supply chains and logistics operations. " * 5
    mock_payload = {
        "results": [
            {
                "url": "https://example.com/report",
                "raw_content": None,
                "content": sample_text,
            }
        ]
    }

    monkeypatch.setattr("app.search.tavily.httpx.post", lambda *args, **kwargs: FakeTavilyResponse(mock_payload))
    tavily = TavilyProvider(Settings(tavily_api_key="tvly-test-key"))
    extracted = tavily.extract("https://example.com/report")
    assert extracted == sample_text

