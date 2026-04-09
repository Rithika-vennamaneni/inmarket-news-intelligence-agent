"""Response models for the agent API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health response payload."""

    status: str
    service: str
    message: str


class SourceAttribution(BaseModel):
    """Article source attribution returned with chat responses."""

    title: str
    source_name: str


class ChatResponse(BaseModel):
    """Chat response payload."""

    conversation_id: str
    response: str
    used_tools: list[str]
    sources: list[SourceAttribution]
