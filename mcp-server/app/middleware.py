"""Middleware configuration and request tracing utilities."""

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import Settings

LOGGER = logging.getLogger("newsapi_mcp.request")


def configure_logging() -> None:
    """Initialize application logging."""
    if logging.getLogger().handlers:
        return
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def add_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """Attach CORS middleware with explicit defaults."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=settings.cors_allowed_methods,
        allow_headers=settings.cors_allowed_headers,
        expose_headers=["X-Request-ID"],
        allow_credentials=False,
    )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and log each request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request and emit a structured access log."""
        started_at = perf_counter()
        request_id = uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        _log_request(request, response.status_code, started_at, request_id)
        return response


def add_request_context_middleware(app: FastAPI) -> None:
    """Attach request tracing middleware."""
    app.add_middleware(RequestContextMiddleware)


def _log_request(request: Request, status_code: int, started_at: float, request_id: str) -> None:
    """Log request metadata and execution time."""
    duration_ms = (perf_counter() - started_at) * 1000
    LOGGER.info(
        "method=%s path=%s status_code=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        status_code,
        duration_ms,
        request_id,
    )
