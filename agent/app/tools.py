"""LangChain tools backed by the MCP server."""

from typing import Any

from langchain_core.tools import StructuredTool

from app.mcp_client import MCPClient
from app.models.tool_inputs import BrandSentimentInput, SearchNewsInput, TopHeadlinesInput


def build_tools(mcp_client: MCPClient) -> list[StructuredTool]:
    """Build the LangChain tools used by the agent."""
    return [_build_search_tool(mcp_client), _build_headlines_tool(mcp_client), _build_sentiment_tool(mcp_client)]


def _build_search_tool(mcp_client: MCPClient) -> StructuredTool:
    """Create the general news search tool."""

    async def search_news(topic: str) -> str:
        """Fetch and format recent news for a topic."""
        payload = await mcp_client.search_news(topic)
        return _format_articles(payload, f"No recent news found about {topic}.")

    return StructuredTool.from_function(
        coroutine=search_news,
        name="search_news",
        description="Search for recent news articles about any topic or event",
        args_schema=SearchNewsInput,
    )


def _build_headlines_tool(mcp_client: MCPClient) -> StructuredTool:
    """Create the top headlines tool."""

    async def get_top_headlines(category: str) -> str:
        """Fetch and format top headlines for a category."""
        payload = await mcp_client.get_top_headlines(category)
        return _format_articles(payload, f"No top headlines found for category {category}.")

    return StructuredTool.from_function(
        coroutine=get_top_headlines,
        name="get_top_headlines",
        description="Get current top headlines by category like business, technology, sports",
        args_schema=TopHeadlinesInput,
    )


def _build_sentiment_tool(mcp_client: MCPClient) -> StructuredTool:
    """Create the brand sentiment analysis tool."""

    async def analyze_brand_sentiment(brand: str) -> str:
        """Fetch and format recent brand coverage."""
        payload = await mcp_client.analyze_brand_sentiment(brand)
        return _format_articles(payload, f"No recent brand news found for {brand}.")

    return StructuredTool.from_function(
        coroutine=analyze_brand_sentiment,
        name="analyze_brand_sentiment",
        description="Get latest news about a specific brand or company to understand public perception",
        args_schema=BrandSentimentInput,
    )


def _format_articles(payload: dict[str, Any], empty_message: str) -> str:
    """Render MCP article payloads into concise tool output."""
    articles = payload.get("articles", [])
    if not articles:
        return empty_message
    return "\n".join(_format_article_lines(articles))


def _format_article_lines(articles: list[dict[str, Any]]) -> list[str]:
    """Format article items for the language model."""
    return [_format_article(index, article) for index, article in enumerate(articles, start=1)]


def _format_article(index: int, article: dict[str, Any]) -> str:
    """Format a single article into one line."""
    title = article.get("title", "Untitled Article")
    source = article.get("source_name", "Unknown Source")
    description = article.get("description") or "No summary available."
    return f"{index}. {title} ({source}) - {description}"
