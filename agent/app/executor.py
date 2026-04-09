"""LangChain agent setup and execution."""

import re
from typing import Any
from uuid import uuid4

from langchain.agents import create_agent
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq

from app.config import Settings
from app.errors import AppError
from app.mcp_client import MCPClient
from app.models.responses import ChatResponse, SourceAttribution
from app.tools import build_tools

SYSTEM_PROMPT = (
    "You are a consumer intelligence assistant powered by real-time news data. "
    "Your job is to help users understand what is happening with brands, markets, "
    "and consumer trends right now. Always use the available tools to fetch real "
    "data before responding. Summarize findings clearly and concisely. If asked "
    "about a brand always use analyze_brand_sentiment. If asked about general "
    "news use search_news. If asked about categories use get_top_headlines. "
    "When calling tools, pass exactly one string argument only. Use "
    '{"topic":"..."} for search_news, {"category":"..."} for get_top_headlines, '
    'and {"brand":"..."} for analyze_brand_sentiment. Do not include any extra keys.'
)


class ConsumerIntelligenceExecutor:
    """Run the LangChain agent with conversation memory."""

    def __init__(self, settings: Settings, mcp_client: MCPClient) -> None:
        """Build the Groq-powered agent executor."""
        self._memory: dict[str, ConversationBufferWindowMemory] = {}
        self._agent = _build_agent_executor(settings, mcp_client)

    async def run(self, message: str, conversation_id: str | None) -> ChatResponse:
        """Execute the agent for a user message."""
        current_id = conversation_id or str(uuid4())
        memory = self._memory.setdefault(current_id, _build_memory())
        history = memory.load_memory_variables({}).get("chat_history", [])
        try:
            result = await self._agent.ainvoke({"messages": _build_messages(history, message)})
        except AppError:
            raise
        except Exception as error:
            raise AppError("Groq request failed. Please try again later.", 502) from error
        messages = result.get("messages", [])
        answer = _extract_answer(messages)
        sources = _extract_sources(messages)
        tools = _extract_tool_names(messages)
        memory.save_context({"input": message}, {"output": answer})
        return ChatResponse(conversation_id=current_id, response=answer, used_tools=tools, sources=sources)


def _build_agent_executor(settings: Settings, mcp_client: MCPClient) -> Any:
    """Create the LangChain agent executor."""
    llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)
    tools = build_tools(mcp_client)
    return create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)


def _build_messages(history: list[BaseMessage], message: str) -> list[BaseMessage]:
    """Build the input message list for the agent."""
    return [*history, HumanMessage(content=message)]


def _build_memory() -> ConversationBufferWindowMemory:
    """Create conversation memory limited to the last five exchanges."""
    return ConversationBufferWindowMemory(
        k=5,
        return_messages=True,
        input_key="input",
        output_key="output",
        memory_key="chat_history",
    )


def _extract_answer(messages: list[BaseMessage]) -> str:
    """Extract the final assistant answer from agent messages."""
    ai_messages = [item for item in messages if isinstance(item, AIMessage)]
    if not ai_messages:
        return "I could not generate a response."
    return str(ai_messages[-1].content)


def _extract_tool_names(messages: list[BaseMessage]) -> list[str]:
    """Extract unique tool names from returned agent messages."""
    names: list[str] = []
    for item in messages:
        if not isinstance(item, AIMessage):
            continue
        for tool_call in item.tool_calls:
            name = tool_call.get("name")
            if isinstance(name, str) and name not in names:
                names.append(name)
    return names


def _extract_sources(messages: list[BaseMessage]) -> list[SourceAttribution]:
    """Extract article source attributions from tool outputs."""
    found: list[SourceAttribution] = []
    for item in messages:
        if isinstance(item, ToolMessage):
            found.extend(_parse_source_items(item.content))
    return _dedupe_sources(found)


def _parse_source_items(content: object) -> list[SourceAttribution]:
    """Parse article source attributions from tool content."""
    if not isinstance(content, str):
        return []
    return [item for line in content.splitlines() for item in [_parse_source_line(line)] if item is not None]


def _parse_source_line(line: str) -> SourceAttribution | None:
    """Parse a single formatted article line into a source attribution."""
    match = re.match(r"^\d+\.\s+(?P<title>.+?)\s+\((?P<source>[^()]+)\)\s+-\s+.+$", line.strip())
    if not match:
        return None
    return SourceAttribution(title=match.group("title"), source_name=match.group("source"))


def _dedupe_sources(items: list[SourceAttribution]) -> list[SourceAttribution]:
    """Deduplicate source attributions while preserving order."""
    seen: set[tuple[str, str]] = set()
    unique: list[SourceAttribution] = []
    for item in items:
        key = (item.title, item.source_name)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
