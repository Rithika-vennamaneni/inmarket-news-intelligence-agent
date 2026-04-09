"""Response models for NewsAPI wrapper endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health endpoint response."""

    status: str
    service: str
    message: str


class ArticleResponse(BaseModel):
    """Cleaned news article response item."""

    source_id: str | None
    source_name: str
    author: str | None
    title: str
    description: str | None
    url: str
    image_url: str | None
    published_at: str | None


class SearchResponse(BaseModel):
    """Response for article search."""

    message: str
    returned_count: int
    articles: list[ArticleResponse]


class TopHeadlinesResponse(BaseModel):
    """Response for top headlines."""

    message: str
    returned_count: int
    articles: list[ArticleResponse]


class SourceResponse(BaseModel):
    """Cleaned news source response item."""

    id: str | None
    name: str
    description: str
    url: str
    category: str
    language: str
    country: str


class SourcesResponse(BaseModel):
    """Response for source listing."""

    message: str
    returned_count: int
    sources: list[SourceResponse]
