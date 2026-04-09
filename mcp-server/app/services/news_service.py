"""Service layer for NewsAPI calls and response cleaning."""

from typing import Any

import httpx
from fastapi import Request

from app.errors import AppError
from app.models.requests import BrandSentimentRequest, SearchRequest, SourcesRequest, TopHeadlinesRequest
from app.models.responses import (
    ArticleResponse,
    SearchResponse,
    SourceResponse,
    SourcesResponse,
    TopHeadlinesResponse,
)


class NewsService:
    """Encapsulate NewsAPI access and response shaping."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Store the shared HTTP client."""
        self._client = client

    async def search_articles(self, params: SearchRequest) -> SearchResponse:
        """Search NewsAPI articles and return cleaned data."""
        payload = await self._fetch("everything", _search_params(params))
        articles = _clean_articles(payload.get("articles", []))
        # This is the current page count after cleaning, not NewsAPI's upstream totalResults value.
        return SearchResponse(message=_article_message(articles), returned_count=len(articles), articles=articles)

    async def get_top_headlines(self, params: TopHeadlinesRequest) -> TopHeadlinesResponse:
        """Fetch top headlines and return cleaned data."""
        payload = await self._fetch("top-headlines", _top_headline_params(params))
        articles = _clean_articles(payload.get("articles", []))
        # This is the current page count after cleaning, not NewsAPI's upstream totalResults value.
        return TopHeadlinesResponse(message=_article_message(articles), returned_count=len(articles), articles=articles)

    async def list_sources(self, params: SourcesRequest) -> SourcesResponse:
        """Fetch available news sources and return cleaned data."""
        payload = await self._fetch("top-headlines/sources", _source_params(params))
        sources = _clean_sources(payload.get("sources", []))
        # This is the current page count after cleaning, not NewsAPI's upstream totalResults value.
        return SourcesResponse(message=_source_message(sources), returned_count=len(sources), sources=sources)

    async def analyze_brand_sentiment(self, params: BrandSentimentRequest) -> SearchResponse:
        """Fetch recent brand coverage for sentiment analysis workflows."""
        payload = await self._fetch("everything", _brand_sentiment_params(params))
        articles = _clean_articles(payload.get("articles", []))
        # This is the current page count after cleaning, not NewsAPI's upstream totalResults value.
        return SearchResponse(message=_article_message(articles), returned_count=len(articles), articles=articles)

    async def _fetch(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call NewsAPI and normalize upstream failures."""
        try:
            response = await self._client.get(endpoint, params=params)
            return _parse_response(response)
        except httpx.TimeoutException as error:
            raise AppError("NewsAPI request timed out.", 504) from error
        except httpx.RequestError as error:
            raise AppError("Unable to reach NewsAPI.", 502) from error
        except ValueError as error:
            raise AppError(str(error), 502) from error


def get_news_service(request: Request) -> NewsService:
    """Create a service instance from the shared client."""
    return NewsService(request.app.state.news_api_client)


def _parse_response(response: httpx.Response) -> dict[str, Any]:
    """Validate the upstream response payload."""
    payload = response.json()
    _raise_for_status(response.status_code, payload)
    if payload.get("status") != "ok":
        raise ValueError("NewsAPI returned an unexpected response.")
    return payload


def _raise_for_status(status_code: int, payload: dict[str, Any]) -> None:
    """Translate upstream status codes into application errors."""
    if status_code == 429 or payload.get("code") == "rateLimited":
        raise AppError("NewsAPI rate limit reached. Please try again later.", 429)
    if status_code in {401, 403}:
        raise AppError("NewsAPI authentication failed. Check NEWS_API_KEY.", 502)
    if status_code == 400:
        raise AppError("NewsAPI rejected the request parameters.", 400)
    if status_code >= 500:
        raise AppError("NewsAPI is unavailable right now.", 502)
    if status_code >= 400:
        raise AppError("NewsAPI returned an unexpected client error.", 502)


def _search_params(params: SearchRequest) -> dict[str, Any]:
    """Build query parameters for article search."""
    query = {"q": params.q, "sortBy": params.sort_by, "page": params.page, "pageSize": params.page_size}
    return _merge_optional(
        query,
        language=params.language,
        from_param=params.from_date.isoformat() if params.from_date else None,
        to=params.to_date.isoformat() if params.to_date else None,
    )


def _top_headline_params(params: TopHeadlinesRequest) -> dict[str, Any]:
    """Build query parameters for top headlines."""
    query = {"page": params.page, "pageSize": params.page_size}
    return _merge_optional(
        query,
        country=params.country,
        category=params.category,
        sources=params.source,
        q=params.q,
    )


def _source_params(params: SourcesRequest) -> dict[str, Any]:
    """Build query parameters for source listing."""
    return _merge_optional({}, category=params.category, language=params.language, country=params.country)


def _brand_sentiment_params(params: BrandSentimentRequest) -> dict[str, Any]:
    """Build query parameters for brand-focused search."""
    return {"q": params.brand, "sortBy": "publishedAt", "page": 1, "pageSize": params.page_size}


def _merge_optional(base: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Merge optional values into a query dictionary."""
    extras = {key.replace("_param", ""): value for key, value in kwargs.items() if value is not None}
    return {**base, **extras}


def _clean_articles(items: list[dict[str, Any]]) -> list[ArticleResponse]:
    """Convert raw article payloads into cleaned response models."""
    return [item for item in (_build_article(entry) for entry in items) if item is not None]


def _build_article(entry: dict[str, Any]) -> ArticleResponse | None:
    """Build a single cleaned article model."""
    url = _clean_text(entry.get("url"))
    if not url:
        return None
    source = entry.get("source") or {}
    return ArticleResponse(
        source_id=_clean_text(source.get("id")),
        source_name=_clean_text(source.get("name")) or "Unknown Source",
        author=_clean_text(entry.get("author")),
        title=_clean_text(entry.get("title")) or "Untitled Article",
        description=_clean_text(entry.get("description")),
        url=url,
        image_url=_clean_text(entry.get("urlToImage")),
        published_at=entry.get("publishedAt"),
    )


def _clean_sources(items: list[dict[str, Any]]) -> list[SourceResponse]:
    """Convert raw source payloads into cleaned response models."""
    return [item for item in (_build_source(entry) for entry in items) if item is not None]


def _build_source(entry: dict[str, Any]) -> SourceResponse | None:
    """Build a single cleaned source model."""
    url = _clean_text(entry.get("url"))
    name = _clean_text(entry.get("name"))
    description = _clean_text(entry.get("description"))
    if not all([url, name, description]):
        return None
    return SourceResponse(
        id=_clean_text(entry.get("id")),
        name=name,
        description=description,
        url=url,
        category=_clean_text(entry.get("category")) or "general",
        language=_clean_text(entry.get("language")) or "unknown",
        country=_clean_text(entry.get("country")) or "unknown",
    )


def _clean_text(value: Any) -> str | None:
    """Trim text values and convert blanks to None."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _article_message(items: list[ArticleResponse]) -> str:
    """Build a user-facing message for article responses."""
    return "Articles retrieved successfully." if items else "No articles found for the requested filters."


def _source_message(items: list[SourceResponse]) -> str:
    """Build a user-facing message for source responses."""
    return "Sources retrieved successfully." if items else "No sources found for the requested filters."
