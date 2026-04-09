"""Configuration for the NewsAPI MCP server."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    news_api_key: str = Field(..., alias="NEWS_API_KEY")
    news_api_base_url: str = "https://newsapi.org/v2/"
    request_timeout_seconds: float = 10.0
    app_name: str = "NewsAPI MCP Server"
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    cors_allowed_methods: list[str] = ["GET", "OPTIONS"]
    cors_allowed_headers: list[str] = ["Authorization", "Content-Type", "X-Request-ID"]
    model_config = SettingsConfigDict(extra="ignore")

    @field_validator("news_api_key")
    @classmethod
    def validate_news_api_key(cls, value: str) -> str:
        """Ensure the NewsAPI key is present and non-empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("NEWS_API_KEY must not be empty.")
        return cleaned

    @field_validator("cors_allowed_origins", "cors_allowed_methods", "cors_allowed_headers", mode="before")
    @classmethod
    def parse_csv_settings(cls, value: str | list[str]) -> list[str]:
        """Normalize list-based settings from strings or lists."""
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]


def _raise_settings_error(error: ValidationError) -> None:
    """Raise a clear startup error for missing environment variables."""
    mapping = {"news_api_key": "NEWS_API_KEY"}
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
