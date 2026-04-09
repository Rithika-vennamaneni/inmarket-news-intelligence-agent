"""Input schemas for LangChain tools."""

from pydantic import BaseModel, Field, field_validator


class SearchNewsInput(BaseModel):
    """Input schema for the search news tool."""

    topic: str = Field(..., description="Topic or event to search for.")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        """Ensure topic input is not empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("topic must not be empty.")
        return cleaned


class TopHeadlinesInput(BaseModel):
    """Input schema for the top headlines tool."""

    category: str = Field(..., description="News category such as business or technology.")

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        """Ensure category input is not empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("category must not be empty.")
        return cleaned


class BrandSentimentInput(BaseModel):
    """Input schema for the brand sentiment tool."""

    brand: str = Field(..., description="Brand or company name.")

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, value: str) -> str:
        """Ensure brand input is not empty."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("brand must not be empty.")
        return cleaned
