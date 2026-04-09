"""Async client for communicating with the MCP news server."""

from typing import Any

import httpx

from app.errors import AppError


class MCPClient:
    """Encapsulate HTTP calls to the MCP server."""

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        """Create an async HTTP client for MCP requests."""
        self._client = httpx.AsyncClient(base_url=_normalize_base_url(base_url), timeout=timeout_seconds)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def search_news(self, topic: str) -> dict[str, Any]:
        """Fetch recent news about a topic."""
        return await self._get("/search", {"q": topic, "page_size": 5})

    async def get_top_headlines(self, category: str) -> dict[str, Any]:
        """Fetch current headlines for a category."""
        return await self._get("/top-headlines", {"country": "us", "category": category, "page_size": 5})

    async def analyze_brand_sentiment(self, brand: str) -> dict[str, Any]:
        """Fetch recent brand news from the MCP server."""
        return await self._get("/sentiment-search", {"brand": brand, "page_size": 5})

    async def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a GET request with one retry on timeout."""
        response = await self._request_with_retry(endpoint, params)
        return _parse_response(response)

    async def _request_with_retry(self, endpoint: str, params: dict[str, Any]) -> httpx.Response:
        """Retry a timed out MCP request once before failing."""
        try:
            return await self._client.get(endpoint, params=params)
        except httpx.TimeoutException:
            return await self._retry_timeout(endpoint, params)
        except httpx.RequestError as error:
            raise AppError("MCP server is unavailable right now.", 502) from error

    async def _retry_timeout(self, endpoint: str, params: dict[str, Any]) -> httpx.Response:
        """Retry a timed out MCP request once."""
        try:
            return await self._client.get(endpoint, params=params)
        except httpx.TimeoutException as error:
            raise AppError("MCP server timed out after retrying once.", 504) from error
        except httpx.RequestError as error:
            raise AppError("MCP server is unavailable right now.", 502) from error


def _parse_response(response: httpx.Response) -> dict[str, Any]:
    """Normalize MCP server responses and failures."""
    payload = _parse_json(response)
    if response.status_code < 400:
        return payload
    message = payload.get("error", "MCP server request failed.")
    raise AppError(message, response.status_code)


def _normalize_base_url(base_url: str) -> str:
    """Ensure the MCP base URL has a trailing slash."""
    return base_url if base_url.endswith("/") else f"{base_url}/"


def _parse_json(response: httpx.Response) -> dict[str, Any]:
    """Parse JSON payloads from MCP responses."""
    try:
        return response.json()
    except ValueError as error:
        raise AppError("MCP server returned an invalid response.", 502) from error
