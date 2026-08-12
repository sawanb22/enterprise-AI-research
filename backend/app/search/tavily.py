import httpx
from ..config import Settings
from ..ai.contracts import ProviderConfigurationError, ProviderError, SearchResult


class TavilyProvider:
    """Tavily web search and content extraction adapter."""

    search_endpoint = "https://api.tavily.com/search"
    extract_endpoint = "https://api.tavily.com/extract"

    def __init__(self, settings: Settings):
        self.api_key = settings.tavily_api_key

    @property
    def headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ProviderConfigurationError("TAVILY_API_KEY is not configured. Add it to the root .env file.")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def search(self, query: str, max_results: int = 3) -> list[SearchResult]:
        try:
            response = httpx.post(
                self.search_endpoint,
                headers=self.headers,
                json={
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False,
                },
                timeout=45,
            )
            response.raise_for_status()
            return [
                SearchResult(
                    url=item["url"],
                    title=item.get("title"),
                    snippet=item.get("content", ""),
                    score=item.get("score"),
                )
                for item in response.json().get("results", [])
                if item.get("url")
            ]
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Tavily search failed ({exc.response.status_code}): {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Tavily search could not be completed: {exc}") from exc

    def extract(self, url: str) -> str:
        try:
            response = httpx.post(
                self.extract_endpoint,
                headers=self.headers,
                json={"urls": [url], "extract_depth": "basic", "include_images": False},
                timeout=60,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                raise ProviderError("Tavily did not return extracted source content.")
            content = results[0].get("raw_content") or results[0].get("content") or ""
            if len(content.strip()) < 200:
                raise ProviderError("Tavily returned too little source content to analyse.")
            return content
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Tavily extraction failed ({exc.response.status_code}): {exc.response.text[:300]}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Tavily extraction could not be completed: {exc}") from exc
