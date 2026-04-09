# Consumer Intelligence Agent

FastAPI service that runs a LangChain agent on top of the MCP news server.

## Run locally

```bash
uvicorn app.main:app --reload --port 8001 --app-dir agent
```
