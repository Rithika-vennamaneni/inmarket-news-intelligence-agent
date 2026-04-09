"""News routes for the application."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.requests import BrandSentimentRequest, SearchRequest, SourcesRequest, TopHeadlinesRequest
from app.models.responses import SearchResponse, SourcesResponse, TopHeadlinesResponse
from app.services.news_service import NewsService, get_news_service

router = APIRouter(tags=["news"])


@router.get("/search", response_model=SearchResponse, response_model_exclude_none=True)
async def search_articles(
    params: Annotated[SearchRequest, Depends()],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> SearchResponse:
    """Search articles through NewsAPI."""
    return await service.search_articles(params)


@router.get("/top-headlines", response_model=TopHeadlinesResponse, response_model_exclude_none=True)
async def top_headlines(
    params: Annotated[TopHeadlinesRequest, Depends()],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> TopHeadlinesResponse:
    """Return cleaned top headlines."""
    return await service.get_top_headlines(params)


@router.get("/sources", response_model=SourcesResponse, response_model_exclude_none=True)
async def list_sources(
    params: Annotated[SourcesRequest, Depends()],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> SourcesResponse:
    """Return cleaned source metadata."""
    return await service.list_sources(params)


@router.get("/sentiment-search", response_model=SearchResponse, response_model_exclude_none=True)
async def sentiment_search(
    params: Annotated[BrandSentimentRequest, Depends()],
    service: Annotated[NewsService, Depends(get_news_service)],
) -> SearchResponse:
    """Return recent brand coverage for sentiment analysis."""
    return await service.analyze_brand_sentiment(params)
