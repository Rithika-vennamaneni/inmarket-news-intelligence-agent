"""Request models for NewsAPI wrapper endpoints."""

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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


class SearchRequest(BaseRequestModel):
    """Query parameters for article search."""

    q: str = Field(..., description="Search query.")
    language: str | None = Field(default=None, pattern="^[a-z]{2}$")
    sort_by: Literal["relevancy", "popularity", "publishedAt"] = "publishedAt"
    from_date: date | None = None
    to_date: date | None = None
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_date_range(self) -> "SearchRequest":
        """Ensure the provided date range is valid."""
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be earlier than or equal to to_date.")
        return self

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        """Normalize the optional language filter."""
        return value.lower() if value else value


class TopHeadlinesRequest(BaseRequestModel):
    """Query parameters for top headlines."""

    country: str | None = Field(default=None, pattern="^[a-z]{2}$")
    category: str | None = Field(default=None, pattern="^[a-zA-Z-]+$")
    source: str | None = None
    q: str | None = None
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_filters(self) -> "TopHeadlinesRequest":
        """Ensure headline filters match NewsAPI rules."""
        has_source = self.source is not None
        has_scope = any([self.country, self.category])
        has_filter = any([has_source, has_scope, self.q])
        if not has_filter:
            raise ValueError("Provide at least one headline filter.")
        if has_source and has_scope:
            raise ValueError("source cannot be combined with country or category.")
        return self

    @field_validator("country", "category")
    @classmethod
    def normalize_filters(cls, value: str | None) -> str | None:
        """Normalize optional headline filter fields."""
        return value.lower() if value else value


class SourcesRequest(BaseRequestModel):
    """Query parameters for source listing."""

    category: str | None = Field(default=None, pattern="^[a-zA-Z-]+$")
    language: str | None = Field(default=None, pattern="^[a-z]{2}$")
    country: str | None = Field(default=None, pattern="^[a-z]{2}$")

    @field_validator("category", "language", "country")
    @classmethod
    def normalize_optional_filters(cls, value: str | None) -> str | None:
        """Normalize optional source filters."""
        return value.lower() if value else value


class BrandSentimentRequest(BaseRequestModel):
    """Query parameters for brand-focused news lookup."""

    brand: str = Field(..., description="Brand or company name.")
    page_size: int = Field(default=10, ge=1, le=25)
