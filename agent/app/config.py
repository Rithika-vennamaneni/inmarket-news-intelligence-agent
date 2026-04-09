"""Configuration for the agent service."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    groq_api_key: str = Field(..., alias="GROQ_API_KEY")
    mcp_server_url: str = Field(..., alias="MCP_SERVER_URL")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    app_name: str = "Consumer Intelligence Agent"
    request_timeout_seconds: float = 10.0
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    model_config = SettingsConfigDict(extra="ignore")

    @field_validator("groq_api_key", "mcp_server_url", "groq_model")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        """Ensure required string settings are not empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Required environment variable must not be empty.")
        return cleaned

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        """Normalize CORS origins from strings or lists."""
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


def _raise_settings_error(error: ValidationError) -> None:
    """Raise a clear startup error for missing environment variables."""
    mapping = {"groq_api_key": "GROQ_API_KEY", "mcp_server_url": "MCP_SERVER_URL"}
    missing = [mapping.get(str(item["loc"][0]), str(item["loc"][0])) for item in error.errors()]
    names = ", ".join(sorted(set(missing)))
    raise RuntimeError(f"Missing required environment variables: {names}") from error


@lru_cache
def get_settings() -> Settings:
    """Load and cache application settings once."""
    try:
        return Settings()
    except ValidationError as error:
        _raise_settings_error(error)
