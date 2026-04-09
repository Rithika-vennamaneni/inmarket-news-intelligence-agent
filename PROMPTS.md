## MCP Server
**Prompt used:**
Build a production-grade MCP Server using FastAPI that wraps the NewsAPI. Create it inside of a mcp-server folder.

SECURITY REQUIREMENTS:
- All API keys loaded via python dotenv from .env file
- Never hardcode any keys anywhere in the code
- .env must be in .gitignore
- Create .env.example with placeholder values:
  NEWS_API_KEY=your_newsapi_key_here
- Validate environment variables exist on startup,
  throw clear error if missing

REQUEST/RESPONSE RULES:
- Use Pydantic models for ALL request and response schemas
- Validate all inputs no empty strings
- Never return raw NewsAPI response  always clean
  and restructure it
- Proper HTTP status codes on all responses
- Return empty list with clear message if no results,
  never crash

ERROR HANDLING:
- Handle NewsAPI rate limits gracefully with clear message
- Handle invalid inputs before hitting the API
- All errors return structured JSON not stack traces:
  {"error": "clear message here"}
- try/except in service layer only, not in routes

CODE PRINCIPLES:
- Routes handle HTTP only and no business logic
- Services handle all NewsAPI calls and data cleaning
- Config loaded once in config.py using 
  pydantic BaseSettings
- Type hints on every single function
- Docstring on every function
- Functions should do one thing only
- No function longer than 20 lines

GITIGNORE MUST INCLUDE:
.env
__pycache__/
.pytest_cache/
venv/
.DS_Store
*.pyc

After generating, provide:
1. How to run locally with uvicorn
2. Example curl command for each endpoint
3. What the cleaned response looks like for /search

**What it generated:**
It generated the FastAPI NewsAPI wrapper with configuration loading, request validation, service-layer API calls, and cleaned response models.

## MCP Middleware and Observability
**Prompt used:**
Middleware & Observability:
- Add request logging middleware that logs method, 
  path, status code and response time for every request
- Add CORS middleware configured properly
- Add request ID to every response header for tracing

**What it generated:**
It added logging, CORS, and request ID middleware to the MCP service.

## Agent Backend
**Prompt used:**
Now build the LangChain Agent backend. This is a 
separate service in a new folder called /agent that 
sits on top of the MCP server we just built running 
on port 8000. This agent runs on port 8001.

Use Groq instead of OpenAI. Import ChatGroq from 
langchain-groq. Use model llama3-8b-8192. 
API key is GROQ_API_KEY in .env

SECURITY REQUIREMENTS:
- All keys loaded via python-dotenv from .env
- .env in .gitignore
- .env.example with placeholders:
  GROQ_API_KEY=your_groq_key_here
  MCP_SERVER_URL=http://localhost:8000
- Never hardcode keys anywhere

TOOLS TO BUILD:
Build 3 LangChain tools that call the MCP server:

Tool 1: search_news
- Description: "Search for recent news articles 
  about any topic or event"
- Input: topic (string)
- Calls MCP /search endpoint
- Returns formatted article summaries

Tool 2: get_top_headlines
- Description: "Get current top headlines by 
  category like business, technology, sports"
- Input: category (string)
- Calls MCP /top-headlines endpoint
- Returns formatted headlines

Tool 3: analyze_brand_sentiment
- Description: "Get latest news about a specific 
  brand or company to understand public perception"
- Input: brand (string)
- Calls MCP /sentiment-search endpoint
- Returns formatted brand news summary

AGENT SETUP:
- Use LangChain AgentExecutor with ChatGroq
- from langchain_groq import ChatGroq
- Model: llama3-8b-8192
- Agent should:
  - Understand natural language queries
  - Decide which tool to use automatically
  - Handle multi-step reasoning if needed
  - Return clean summarized response not raw data

SYSTEM PROMPT FOR AGENT:
"You are a consumer intelligence assistant powered 
by real-time news data. Your job is to help users 
understand what is happening with brands, markets, 
and consumer trends right now. Always use the 
available tools to fetch real data before responding. 
Summarize findings clearly and concisely. If asked 
about a brand always use analyze_brand_sentiment. 
If asked about general news use search_news. 
If asked about categories use get_top_headlines."

CONVERSATION MEMORY:
- Maintain conversation history per conversation_id
- Use LangChain ConversationBufferWindowMemory
- Keep last 5 exchanges only to control token usage
- If no conversation_id provided generate new uuid

MCP CLIENT SERVICE:
- Build clean async httpx client in mcp_client.py
- All calls to MCP server go through this service only
- Handle MCP server being unavailable gracefully
- Timeout after 10 seconds on MCP calls
- Retry once on timeout before failing

ERROR HANDLING:
- If MCP server is down return clear message to user
- If Groq API fails return clear message
- If tool returns no results agent should say so
  naturally not crash
- All errors follow same response envelope as MCP server

MIDDLEWARE:
- Request logging middleware logging method, path,
  status code and response time
- CORS configured for frontend on localhost:3000
- Request ID on every response header for tracing

CODE PRINCIPLES:
- tools.py only defines tools
- executor.py only sets up and runs the agent
- mcp_client.py only handles HTTP to MCP server
- routes only handle HTTP in and out
- Type hints on every function
- Docstrings on every function
- No function longer than 20 lines

REQUIREMENTS.TXT:
fastapi
uvicorn
python-dotenv
pydantic
pydantic-settings
httpx
langchain
langchain-groq
langchain-community
groq
pytest
pytest-asyncio

After generating provide:
1. How to run locally on port 8001
2. Example curl command for /chat endpoint
3. Show me what happens step by step when user 
   asks "what is happening with Tesla today"

**What it generated:**
It generated the separate agent backend with LangChain tools, Groq model integration, conversation memory, and an MCP client service.

## Frontend
**Prompt used:**
Now build the frontend in a new folder called /frontend.
React with TypeScript. Runs on port 3000.
Talks to agent backend on http://localhost:8001/chat

UI REQUIREMENTS:
- Clean chat interface, messages on left and right
  like iMessage style
- User messages on right, agent responses on left
- Show which tools were used under each 
  agent response in small gray text
  e.g. "used: analyze_brand_sentiment"
- Loading spinner while waiting for response
- Disable input while request is in progress
- Persist conversation_id in useState so memory works
  across messages in the same session

SUGGESTED STARTER QUERIES:
- Show 3 clickable suggestion chips on load:
  "What's happening with Tesla today"
  "Top business headlines right now"
  "What are consumers saying about Apple"
- Chips disappear once first message is sent

TECHNICAL REQUIREMENTS:
- Use fetch not axios
- Handle errors gracefully — show error message
  in chat if request fails
- Tailwind CSS for styling
- No external component libraries
- Single App.tsx file is fine

STYLE:
- Dark theme
- Clean and minimal
- Professional not flashy

**What it generated:**
It generated the React frontend with chat state, loading handling, conversation continuity, and a Tailwind-based interface.

## Frontend Empty State Simplification
**Prompt used:**
Simplify the empty state UI.
Remove the START HERE card entirely.
Just show a single line of subtle gray text saying:
"Powered by live news via NewsAPI"
Then show the 3 suggestion chips below it.
Nothing else.

**What it generated:**
It removed the original empty-state card and replaced it with a minimal message plus suggestion chips.

## Frontend Vertical Centering
**Prompt used:**
Add more vertical spacing between the heading 
and the suggestion chips. Center everything 
vertically in the chat area not at the top.

**What it generated:**
It centered the empty state vertically and increased the spacing between the heading and suggestion chips.

## Agent Response Sources
**Prompt used:**
After each agent response show a "Sources" section
with bullet points listing the article titles and 
source names returned by the news tool.
Extract these from the tools_used response data.
Style them as small subtle gray text with a 
"Sources:" label above them.

**What it generated:**
It added source attribution extraction in the agent backend and rendered a `Sources:` block under assistant messages in the frontend.

## MCP Count Rename
**Prompt used:**
In news_service.py rename total_results to 
returned_count everywhere it uses len(articles) 
or len(sources). Add a comment explaining this 
is page count not NewsAPI totalResults.

**What it generated:**
It renamed the response field to `returned_count` and documented the difference between page count and upstream total result count.

## Frontend Backend URL Configuration
**Prompt used:**
In App.tsx move the backend URL to an 
environment variable.
const ENDPOINT = import.meta.env.VITE_API_URL 
|| "http://localhost:8001/chat"
Add VITE_API_URL=http://localhost:8001/chat 
to frontend .env.example

**What it generated:**
It moved the frontend chat endpoint into a Vite environment variable and added a frontend env example file.

## Frontend Non-JSON Error Handling
**Prompt used:**
In App.tsx wrap response.json() in a try/catch.
If JSON parsing fails show a generic error 
message in chat instead of crashing.

**What it generated:**
It added guarded JSON parsing so malformed or non-JSON backend responses surface as a generic chat error instead of a frontend crash.
