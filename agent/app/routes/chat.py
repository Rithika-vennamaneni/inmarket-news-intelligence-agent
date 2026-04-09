"""Chat routes for the agent service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.executor import ConsumerIntelligenceExecutor
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse

router = APIRouter(tags=["chat"])


def get_executor(request: Request) -> ConsumerIntelligenceExecutor:
    """Return the shared agent executor from app state."""
    return request.app.state.agent_executor


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    executor: Annotated[ConsumerIntelligenceExecutor, Depends(get_executor)],
) -> ChatResponse:
    """Run the consumer intelligence agent."""
    return await executor.run(payload.message, payload.conversation_id)
