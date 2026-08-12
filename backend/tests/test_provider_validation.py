import json

from app.config import Settings
from app.providers import GroqProvider


class FakeResponse:
    def __init__(self, content):
        self.content = content
        self.text = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


def test_plan_repairs_one_invalid_structured_response(monkeypatch):
    responses = iter(
        [
            FakeResponse(json.dumps({"unexpected": "shape"})),
            FakeResponse(json.dumps({"sub_questions": ["What changes?"], "search_queries": ["AI retail operations research"]})),
        ]
    )
    monkeypatch.setattr("app.providers.httpx.post", lambda *args, **kwargs: next(responses))
    provider = GroqProvider(Settings(groq_api_key="test-key"))
    plan = provider.plan("How is AI transforming retail operations?", 1)
    assert plan["search_queries"] == ["AI retail operations research"]
    assert provider.repair_count == 1
