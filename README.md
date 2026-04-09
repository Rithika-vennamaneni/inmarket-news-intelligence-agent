# News Intelligence Chat

## Overview
This project provides a news-driven chat system for brand, market, and category analysis. It separates article retrieval, tool orchestration, and user interface concerns so each layer can be developed, tested, and deployed independently. The system exists to turn live news data into structured, queryable summaries through a chat workflow.

## Architecture
The system is split into three services so that external news access, LLM orchestration, and frontend delivery remain isolated. This keeps API credentials scoped to the services that need them, reduces coupling between UI and backend logic, and makes it possible to deploy or scale each layer independently.

```text
User → Frontend (3000)
          ↓
    Agent Backend (8001)
    [LangChain + Groq llama3]
          ↓
    MCP Server (8000)
    [NewsAPI Wrapper]
          ↓
       NewsAPI
```

The frontend is a React application that manages the chat session, sends user messages to the agent backend, and renders summaries, tool usage, and article source attributions. The agent backend owns conversation memory, tool selection, LLM calls, and all orchestration logic. The MCP server is a dedicated NewsAPI wrapper that validates inputs, normalizes upstream failures, and returns cleaned response shapes instead of raw NewsAPI payloads.

## Prerequisites
You need Python 3.11 or newer, Node.js 18 or newer, and npm 9 or newer.

Get API keys from these providers:
- NewsAPI: `https://newsapi.org` (free tier)
- Groq: `https://console.groq.com` (free tier)

## Setup & Running

### 1. Clone and structure
```bash
git clone <repository-url>
cd <repository-directory>
```

The repository should contain these top-level directories:
```text
agent/
frontend/
mcp-server/
```

### 2. MCP Server
```bash
cd mcp-server
cp .env.example .env
# add NEWS_API_KEY to .env
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

### 3. Agent Backend
```bash
cd agent
cp .env.example .env
# add GROQ_API_KEY to .env
pip install -r requirements.txt
uvicorn app.main:app --port 8001
```

### 4. Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Note: All 3 services must run simultaneously in separate terminals.

## Environment Variables

| Variable | Service | Description |
| --- | --- | --- |
| `NEWS_API_KEY` | MCP Server | Required NewsAPI key used for all upstream article and source requests. |
| `NEWS_API_BASE_URL` | MCP Server | Optional base URL override for NewsAPI. Defaults to `https://newsapi.org/v2/`. |
| `REQUEST_TIMEOUT_SECONDS` | MCP Server | Optional HTTP timeout for upstream NewsAPI calls. |
| `APP_NAME` | MCP Server | Optional FastAPI application title. |
| `CORS_ALLOWED_ORIGINS` | MCP Server | Optional comma-separated list of allowed frontend origins. |
| `CORS_ALLOWED_METHODS` | MCP Server | Optional comma-separated list of allowed CORS methods. |
| `CORS_ALLOWED_HEADERS` | MCP Server | Optional comma-separated list of allowed CORS headers. |
| `GROQ_API_KEY` | Agent Backend | Required Groq API key used for chat model requests. |
| `MCP_SERVER_URL` | Agent Backend | Required base URL for the MCP server, usually `http://localhost:8000`. |
| `GROQ_MODEL` | Agent Backend | Optional Groq model name. The current default in code is `llama-3.3-70b-versatile`. |
| `REQUEST_TIMEOUT_SECONDS` | Agent Backend | Optional timeout used for MCP server HTTP calls. |
| `APP_NAME` | Agent Backend | Optional FastAPI application title. |
| `CORS_ALLOWED_ORIGINS` | Agent Backend | Optional comma-separated list of allowed frontend origins. |
| `VITE_API_URL` | Frontend | Chat endpoint used by the browser. For local development use `http://localhost:8001/chat`. |

## API Reference

### MCP Server

| Method | Endpoint | Description | Example payload |
| --- | --- | --- | --- |
| `GET` | `/health` | Service health check. | `GET /health` |
| `GET` | `/search` | Search recent articles by free-text query. | `GET /search?q=tesla&language=en&page=1&page_size=5` |
| `GET` | `/top-headlines` | Fetch top headlines by category, source, country, or query. | `GET /top-headlines?country=us&category=business&page_size=5` |
| `GET` | `/sentiment-search` | Fetch recent brand-specific coverage for sentiment review. | `GET /sentiment-search?brand=Tesla&page_size=5` |
| `GET` | `/sources` | List available news sources filtered by country, language, or category. | `GET /sources?country=us&language=en` |

`/search` response shape:
```json
{
  "message": "Articles retrieved successfully.",
  "returned_count": 2,
  "articles": [
    {
      "source_id": "cnn",
      "source_name": "CNN",
      "author": "Jane Doe",
      "title": "Tesla announces new model",
      "description": "A short cleaned summary of the article.",
      "url": "https://example.com/article-1",
      "image_url": "https://example.com/image-1.jpg",
      "published_at": "2026-04-08T12:00:00Z"
    }
  ]
}
```

### Agent Backend

`POST /chat`

Request:
```json
{
  "message": "What's happening with Tesla today",
  "conversation_id": "optional-existing-id"
}
```

Response:
```json
{
  "conversation_id": "uuid-string",
  "response": "Tesla coverage today is focused on ...",
  "used_tools": ["analyze_brand_sentiment"],
  "sources": [
    {
      "title": "Tesla announces new model",
      "source_name": "CNN"
    }
  ]
}
```

## How a Request Works
1. The user types `What's happening with Tesla today` in the frontend running on port `3000`.
2. The frontend sends a `POST /chat` request to `VITE_API_URL`, which points to the agent backend on port `8001`.
3. The agent backend validates the request body and loads the existing conversation window if a `conversation_id` was already assigned.
4. The agent backend builds the LangChain message list from the stored chat history plus the new user message.
5. Groq receives the prompt and decides which tool to call. For a brand query it should select `analyze_brand_sentiment`.
6. The `analyze_brand_sentiment` tool calls the MCP client, which sends `GET /sentiment-search?brand=Tesla&page_size=5` to the MCP server on port `8000`.
7. The MCP server validates the query parameters, calls NewsAPI, handles upstream errors, and reshapes the article data into the cleaned MCP response schema.
8. The tool formats the returned articles into compact article summaries for the agent and the agent backend extracts article titles and source names for the `sources` field.
9. Groq produces the final natural-language answer using the tool output, and the agent backend stores the exchange in the in-process conversation memory buffer.
10. The agent backend returns the answer, `conversation_id`, `used_tools`, and `sources` to the frontend, which renders the response bubble and source attribution list.

## Deployment Notes
Each service should be containerized separately. Give the MCP server, agent backend, and frontend their own Dockerfiles, then use a `docker-compose.yml` file to run the full stack locally or in a shared deployment environment. In production, inject secrets through the container platform or a secrets manager. Do not ship `.env` files with deployed images.

The MCP server and agent backend are good fits for AWS ECS or Google Cloud Run because both are stateless HTTP services when conversation state is externalized. The frontend is a standard static SPA and fits Vercel or Netlify. For production conversation state, replace the in-memory conversation dict with Redis plus a TTL so conversation history survives process restarts and can be shared across multiple backend instances.

Keep API keys in environment-backed secret stores only. Restrict CORS to known frontend domains instead of local development defaults. Upstream NewsAPI rate limit handling is already implemented in the MCP layer, but you still need service-level rate limiting and request controls at the edge for public deployment.

## Known Limitations
- Conversation memory is in-process only. Does not persist across restarts. Production fix: Redis with TTL.
- NewsAPI free tier limits to 100 requests/day and excludes articles older than 1 month.
- Frontend backend URL must be set via `VITE_API_URL` env var for non-local deployment.

## Development Notes
- Agentic IDE used: GitHub Copilot
- LLM for summarization: Groq llama3-8b-8192
- All prompts used during development are documented in `PROMPTS.md`
