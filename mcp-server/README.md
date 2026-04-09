# NewsAPI MCP Server

FastAPI server that wraps NewsAPI and returns cleaned, validated JSON responses.

## Run locally

1. Create a virtual environment and install dependencies.
2. Copy `.env.example` to `.env`.
3. Start the server:

```bash
uvicorn app.main:app --reload --app-dir mcp-server
```

## Endpoints

- `GET /health`
- `GET /search`
- `GET /top-headlines`
- `GET /sources`
