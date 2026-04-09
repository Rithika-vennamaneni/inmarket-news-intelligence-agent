# Development Approach

I built this system in four phases, each with a 
focused prompt and a clear output goal. Before 
writing any prompt I mapped the full architecture 
so each service had a defined responsibility. 
After each phase I ran a code audit before moving 
to the next one, so structural problems got caught 
early instead of compounding.

The three decisions that shaped how I prompted:

1. Front-load architecture rules into phase 1. 
   If separation of concerns isn't enforced from 
   the first generation, you spend the rest of 
   the build fixing structure instead of adding 
   value.

2. Write precise tool descriptions for the agent. 
   The LLM reads tool descriptions to decide which 
   tool to call. Vague descriptions cause wrong 
   tool selection. Specific ones don't.

3. Use Groq instead of OpenAI. Free tier, faster 
   responses, and no cost constraints during 
   development or demo recording.


## Phase 1 — MCP Server

**Why I started here:**
The MCP server is the foundation everything else 
depends on. If the NewsAPI wrapper returns 
inconsistent shapes or leaks raw upstream errors, 
every layer above it breaks in unpredictable ways. 
I built and verified this first before touching 
the agent or frontend.

**Decision I made:**
I included security requirements, error handling 
rules, and code principles directly in the prompt 
rather than fixing them after generation. The goal 
was to get production-grade scaffolding on the 
first pass, not iterate toward it.

**Prompt used:**
Build a production-grade MCP Server using FastAPI 
that wraps the NewsAPI. Create it inside a 
mcp-server folder.

SECURITY REQUIREMENTS:
- All API keys loaded via python-dotenv from .env
- Never hardcode any keys anywhere in the code
- .env must be in .gitignore
- Create .env.example with placeholder values:
  NEWS_API_KEY=your_newsapi_key_here
- Validate environment variables exist on startup,
  throw clear error if missing

ENDPOINTS TO BUILD:
1. GET /health — health check
2. POST /search — search by topic
3. POST /top-headlines — headlines by category
4. POST /sentiment-search — brand-focused coverage

REQUEST/RESPONSE RULES:
- Use Pydantic models for ALL request and 
  response schemas
- Validate all inputs, no empty strings
- Never return raw NewsAPI response
- Proper HTTP status codes on all responses
- Return empty list with clear message if no 
  results, never crash

ERROR HANDLING:
- Handle NewsAPI rate limits gracefully
- All errors return structured JSON not stack traces
- try/except in service layer only, not in routes

CODE PRINCIPLES:
- Routes handle HTTP only, no business logic
- Services handle all NewsAPI calls and cleaning
- Config loaded once in config.py using 
  pydantic BaseSettings
- Type hints on every function
- Docstring on every function
- Functions do one thing only
- No function longer than 20 lines

**What it generated:**
FastAPI MCP server with clean service separation,
Pydantic request and response models, structured 
error responses, and startup validation for 
environment variables.


## Phase 1b — MCP Middleware and Observability

**Why I added this separately:**
Observability is not optional in a system with 
multiple services. Without request logging and 
request IDs, debugging cross-service failures 
means guessing. I added this as a focused second 
prompt rather than bloating the first one.

**Prompt used:**
Add to the MCP server:
- Request logging middleware that logs method, 
  path, status code, and response time for 
  every request
- CORS middleware configured properly
- X-Request-ID header on every response for 
  distributed tracing

**What it generated:**
Logging middleware, CORS configuration, and 
request ID injection on all responses.


## Phase 2 — Agent Backend

**Why I approached it this way:**
The agent is the most complex service because 
it owns tool selection, LLM calls, and 
conversation memory simultaneously. I chose 
Groq over OpenAI for two reasons: the free tier 
removes cost constraints, and llama3 handles 
tool calling reliably with LangChain.

**Decision I made on tool descriptions:**
I spent more time on tool descriptions than any 
other part of this prompt. The agent decides 
which tool to call by reading those descriptions. 
I made them specific enough that the right tool 
gets selected for brand queries, category queries, 
and general search without any conditional logic 
in my code.

**Decision I made on memory:**
ConversationBufferWindowMemory with a window of 5 
keeps token usage predictable. I documented the 
known limitation — in-process memory doesn't 
survive restarts — rather than hiding it. 
Production fix is Redis with a TTL.

**Prompt used:**
Build the LangChain Agent backend in a new folder 
called /agent. Separate service running on port 
8001. Calls MCP server on port 8000.

Use Groq. Import ChatGroq from langchain-groq. 
Model: llama3-8b-8192. API key is GROQ_API_KEY.

TOOLS TO BUILD:
Tool 1: search_news
- Description: "Search for recent news articles 
  about any topic or event"
- Calls MCP /search

Tool 2: get_top_headlines  
- Description: "Get current top headlines by 
  category like business, technology, sports"
- Calls MCP /top-headlines

Tool 3: analyze_brand_sentiment
- Description: "Get latest news about a specific 
  brand or company to understand public perception"
- Calls MCP /sentiment-search

AGENT SETUP:
- LangChain AgentExecutor with ChatGroq
- Agent decides tool selection automatically
- ConversationBufferWindowMemory, last 5 exchanges
- Generate UUID if no conversation_id provided

MCP CLIENT:
- Async httpx client in mcp_client.py
- All MCP calls go through this service only
- 10 second timeout, retry once on timeout

CODE PRINCIPLES:
- tools.py defines tools only
- executor.py sets up and runs agent only
- mcp_client.py handles MCP HTTP only
- Routes handle HTTP in and out only

**What it generated:**
Agent backend with 3 LangChain tools, Groq 
integration, per-conversation memory, MCP client 
service, and consistent error envelope matching 
the MCP server.


## Phase 3 — Frontend

**Why I kept this prompt minimal:**
The frontend is the least complex layer. Its only 
job is to send messages and render responses. 
I deliberately kept the prompt focused on 
behavior and structure, not visual design, 
because the evaluation is on architecture not CSS.

**Decision I made:**
Showing tool usage and sources under each agent 
response was not in the original requirements. 
I added it because InMarket's business is 
consumer intelligence — showing where data comes 
from is directly relevant to how they think 
about information quality.

**Prompt used:**
Build the frontend in /frontend. React with 
TypeScript. Port 3000. Calls agent on 
http://localhost:8001/chat.

- iMessage-style chat, user right, agent left
- Show used_tools under each agent response
- Show sources under each agent response
- Loading spinner while waiting
- Disable input during request
- Persist conversation_id in useState
- 3 suggestion chips on load, disappear after 
  first message
- fetch not axios
- Tailwind CSS, no component libraries
- Dark theme, minimal, professional

**What it generated:**
React TypeScript chat interface with conversation 
state, loading handling, source attribution 
rendering, and suggestion chips.


## Phase 4 — Iterative Fixes After Code Audit

**Why I ran a code audit:**
Before pushing I ran a full audit to catch issues 
I wouldn't spot in normal development. I treated 
the audit output as a prioritized fix list, not 
a checklist to clear completely.

**What I fixed and why:**

Frontend backend URL hardcoded — broke any 
non-local deployment. Moved to VITE_API_URL 
environment variable.

total_results semantically wrong — was returning 
page count not NewsAPI total. Renamed to 
returned_count and documented the difference.

Non-JSON error handling — frontend assumed all 
responses were JSON. Added try/catch so malformed 
responses surface as a chat error not a crash.

**What I left alone and why:**
In-process conversation memory — acceptable for 
local demo, documented the production fix instead 
of over-engineering for a non-production context.

Function length in frontend — refactoring 
App.tsx for line count would risk breaking 
working UI with no meaningful benefit.

Deprecated LangChain memory path — it works, 
migration is a maintenance task not a 
correctness issue.
