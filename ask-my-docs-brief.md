# Ask My Docs — Build Brief

## Overview

Build a document Q&A application with three deliverables:

1. A **RAG backend** with a self-correcting retrieval pipeline orchestrated by **LangGraph**
2. An **MCP server** exposing the RAG capabilities as tools, usable from Claude Desktop or any MCP client
3. A minimal **Next.js chat frontend**

The goal is a clean, production-quality portfolio project — not a toy. Prioritise code quality, typing, tests, and documentation over feature breadth.

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language (backend) | Python 3.12 | `uv` for dependency management |
| API framework | FastAPI | async, Pydantic v2 models throughout |
| Orchestration | LangGraph (latest stable) | explicit `StateGraph`, typed state |
| LLM | Anthropic Claude (via `anthropic` SDK or `langchain-anthropic`) | model configurable via env |
| Embeddings | OpenAI `text-embedding-3-small` | abstract behind an interface so it's swappable |
| Vector store | Chroma (persistent, local) | abstract behind a `VectorStore` interface; document how to swap to pgvector |
| Document parsing | `pypdf` for PDF, plain read for md/txt | chunking via LangChain `RecursiveCharacterTextSplitter` (~800 tokens, 150 overlap) |
| MCP server | Official MCP Python SDK (`mcp` package, FastMCP style) | stdio transport |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind | minimal chat UI, streaming responses |
| Testing | pytest + pytest-asyncio | unit tests for chunking, graph routing logic, retrieval grading |
| Lint/format | ruff, mypy (strict on core modules) | pre-commit config |
| Config | pydantic-settings, `.env.example` provided | no hardcoded keys ever |

## Repository Structure

```
ask-my-docs/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routes
│   │   ├── config.py            # pydantic-settings
│   │   ├── ingestion/
│   │   │   ├── loader.py        # file -> text (pdf, md, txt)
│   │   │   └── chunker.py       # splitting logic
│   │   ├── retrieval/
│   │   │   ├── store.py         # VectorStore interface + Chroma impl
│   │   │   └── embedder.py      # Embedder interface + OpenAI impl
│   │   ├── graph/
│   │   │   ├── state.py         # TypedDict / Pydantic graph state
│   │   │   ├── nodes.py         # router, retrieve, grade, rewrite, generate
│   │   │   └── build.py         # StateGraph assembly, compiled graph
│   │   └── api/
│   │       ├── routes_docs.py   # POST /documents (upload), GET /documents, DELETE
│   │       └── routes_chat.py   # POST /chat (SSE streaming)
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
├── mcp-server/
│   ├── server.py                # FastMCP server: query_documents, add_document, list_documents tools
│   └── README.md                # incl. Claude Desktop config snippet
├── frontend/
│   ├── (Next.js app)
│   └── README.md
├── .env.example
├── docker-compose.yml           # backend + frontend, one command up
└── README.md                    # top-level: architecture diagram, quickstart, demo GIF placeholder
```

## LangGraph Pipeline (the core of the project)

Implement an **agentic, self-correcting RAG graph** — not a naive retrieve-then-generate chain.

**State** (typed): `question`, `original_question`, `route`, `retrieved_docs`, `relevance_grade`, `rewrite_count`, `answer`, `sources`.

**Nodes:**

1. **router** — classify the question: `needs_retrieval` vs `general`. General questions skip retrieval and go straight to generate (with a note that no documents were consulted).
2. **retrieve** — top-k similarity search (k=5) against the vector store.
3. **grade_documents** — LLM-as-judge: are the retrieved chunks sufficient/relevant to answer? Output structured (`sufficient: bool`, per-chunk relevance). Use structured output / tool calling, not string parsing.
4. **rewrite_query** — if insufficient, rewrite the question for better retrieval and loop back to **retrieve**. Hard cap: max 2 rewrites (`rewrite_count`), then proceed to generate with a "limited context" flag.
5. **generate** — answer grounded in retrieved chunks, with inline source citations (filename + chunk reference). If context was insufficient, say so explicitly rather than hallucinating.

**Edges:** conditional edges from router and grade_documents; the rewrite loop must be bounded. Export a Mermaid diagram of the compiled graph into the README (LangGraph supports `get_graph().draw_mermaid()`).

## MCP Server

Expose three tools via the official MCP Python SDK (FastMCP decorators):

- `query_documents(question: str) -> str` — runs the full LangGraph pipeline, returns answer + sources
- `add_document(path: str) -> str` — ingest a local file
- `list_documents() -> list` — list indexed documents with chunk counts

The MCP server should import and reuse the backend's graph and ingestion modules (shared package), not duplicate logic. Include a ready-to-paste `claude_desktop_config.json` snippet in the README and a short "demo in Claude Desktop" walkthrough.

## API (FastAPI)

- `POST /documents` — multipart upload (pdf/md/txt), ingest, return doc id + chunk count
- `GET /documents`, `DELETE /documents/{id}`
- `POST /chat` — body `{question, session_id?}`, respond via SSE streaming; final event includes sources
- `GET /health`
- CORS configured for the frontend origin; request/response models all Pydantic; proper error handling with structured error responses (no bare 500s).

## Frontend (keep it thin)

- Single-page chat interface: message list, streaming assistant responses, source citations rendered as expandable chips under each answer
- Document sidebar: upload (drag-drop), list, delete
- No auth needed. Clean, minimal design. Loading and error states handled.

## Engineering Standards (non-negotiable)

- Type hints everywhere; mypy passes on `app/graph` and `app/retrieval`
- Unit tests for: chunker behaviour, router classification (mock LLM), grade→rewrite loop bounding, vector store interface (in-memory fake)
- Ruff clean; pre-commit hooks configured
- Structured logging (`structlog` or stdlib logging with JSON option) — log each graph node transition with timing
- All secrets via env; `.env.example` documents every variable
- Conventional commits; sensible commit history (build in logical increments, not one mega-commit)
- Top-level README: what it is, architecture diagram (Mermaid), quickstart (`docker compose up`), MCP setup for Claude Desktop, screenshot/GIF section, "design decisions" section explaining the self-correcting retrieval loop and the bounded rewrite

## Build Order

1. Backend skeleton: config, ingestion, vector store, tests for chunker
2. LangGraph pipeline with tests (mock LLM for routing/grading tests)
3. FastAPI routes + SSE streaming
4. MCP server reusing the graph
5. Frontend
6. Docker compose, README polish, Mermaid graph export

## Out of Scope (do not build)

Auth, multi-user support, cloud deployment configs beyond docker-compose, evaluation harnesses, multiple vector DB implementations (interface only), conversation memory beyond a single session's messages.
