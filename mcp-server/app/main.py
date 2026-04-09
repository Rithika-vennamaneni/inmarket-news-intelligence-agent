"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.errors import AppError, app_error_handler, generic_error_handler, validation_error_handler
from app.middleware import add_cors_middleware, add_request_context_middleware, configure_logging
from app.routes.health import router as health_router
from app.routes.news import router as news_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize shared application resources."""
    settings = get_settings()
    app.state.news_api_client = httpx.AsyncClient(
        base_url=settings.news_api_base_url,
        headers={"X-Api-Key": settings.news_api_key},
        timeout=settings.request_timeout_seconds,
    )
    yield
    await app.state.news_api_client.aclose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    add_cors_middleware(app, settings)
    add_request_context_middleware(app)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
    app.include_router(health_router)
    app.include_router(news_router)
    return app


app = create_app()
