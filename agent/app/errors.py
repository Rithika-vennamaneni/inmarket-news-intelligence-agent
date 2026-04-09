"""Application error types and handlers."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Structured error response body."""

    error: str


class AppError(Exception):
    """Structured application exception."""

    def __init__(self, message: str, status_code: int) -> None:
        """Store the error message and status code."""
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _format_location(parts: tuple[object, ...]) -> str:
    """Build a readable error location string."""
    filtered = [str(part) for part in parts if part not in {"query", "body", "path"}]
    return ".".join(filtered)


def _format_validation_error(exc: RequestValidationError) -> str:
    """Extract a clear request validation error message."""
    item = exc.errors()[0]
    location = _format_location(tuple(item.get("loc", ())))
    prefix = f"{location}: " if location else ""
    return f"{prefix}{item.get('msg', 'Invalid request.')}"


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Return structured JSON for application errors."""
    payload = ErrorResponse(error=exc.message).model_dump()
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return structured JSON for validation failures."""
    payload = ErrorResponse(error=_format_validation_error(exc)).model_dump()
    return JSONResponse(status_code=422, content=payload)


async def generic_error_handler(_: Request, __: Exception) -> JSONResponse:
    """Return structured JSON for unexpected failures."""
    payload = ErrorResponse(error="Internal server error.").model_dump()
    return JSONResponse(status_code=500, content=payload)
