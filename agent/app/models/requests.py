"""Request models for the agent API."""

from typing import Any

from pydantic import BaseModel, field_validator


class BaseRequestModel(BaseModel):
    """Base request model that rejects empty strings."""

    @field_validator("*", mode="before")
    @classmethod
    def strip_and_reject_empty(cls, value: Any) -> Any:
        """Trim string fields and reject blank values."""
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("String fields must not be empty.")
        return cleaned


class ChatRequest(BaseRequestModel):
    """Input payload for the chat endpoint."""

    message: str
    conversation_id: str | None = None
