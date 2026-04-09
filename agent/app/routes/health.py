"""Health routes for the agent service."""

from fastapi import APIRouter

from app.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return the health status of the service."""
    return HealthResponse(
        status="ok",
        service="consumer-intelligence-agent",
        message="Service is ready.",
    )
