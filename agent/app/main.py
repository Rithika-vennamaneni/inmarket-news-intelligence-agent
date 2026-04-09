"""FastAPI application entrypoint for the agent service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.errors import AppError, app_error_handler, generic_error_handler, validation_error_handler
from app.executor import ConsumerIntelligenceExecutor
from app.mcp_client import MCPClient
from app.middleware import add_cors_middleware, add_request_context_middleware, configure_logging
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize shared application resources."""
    settings = get_settings()
    mcp_client = MCPClient(settings.mcp_server_url, settings.request_timeout_seconds)
    app.state.mcp_client = mcp_client
    app.state.agent_executor = ConsumerIntelligenceExecutor(settings, mcp_client)
    yield
    await mcp_client.close()


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
    app.include_router(chat_router)
    return app


app = create_app()
