# Build Log

Running log of what shipped per phase. See [AGENTS.md](AGENTS.md) for the workflow and [ask-my-docs-brief.md](ask-my-docs-brief.md) for the spec.

## Setup — 2026-07-03

- Added `CLAUDE.md`, `ask-my-docs-brief.md`, `AGENTS.md`.
- Workflow: plan mode per phase → user accepts → Sonnet executes → manual review (graph module always reviewed regardless of author) → update this file → commit.
- Next: Phase 1 — backend skeleton (config, ingestion, vector store, chunker tests).

## Phase 1 — Backend skeleton — 2026-07-04

Branch: `phase-1-backend-skeleton`.

- Toolchain: installed `uv`, pinned Python 3.12.10 (machine default is 3.14, which lacks wheels for some deps here). `backend/pyproject.toml` + `uv.lock` committed.
- `app/config.py` — pydantic-settings `Settings` (LLM/embedding/chunking/retrieval/CORS config), `.env.example` documents every var.
- `app/logging.py` — structlog, JSON/console renderer toggle via `LOG_JSON`.
- `app/ingestion/loader.py` + `chunker.py` — pdf/md/txt loading, `RecursiveCharacterTextSplitter`-backed `chunk_text` producing typed `Chunk` (source + chunk_index for later citations).
- `app/retrieval/embedder.py` — `Embedder` protocol + `OpenAIEmbedder`.
- `app/retrieval/store.py` — `VectorStore` ABC with `ChromaVectorStore` (persistent) and `InMemoryVectorStore` (pure-Python cosine similarity, used in tests). Needed a few targeted `# type: ignore[arg-type]` where chromadb's stubs are narrower than the plain `list[list[float]]`/metadata shapes we pass — noted inline.
- `app/main.py` — FastAPI app, lifespan-based startup logging, CORS, `GET /health`. `/documents` and `/chat` routes deferred to Phase 3 per plan.
- 10 tests passing (chunker, in-memory store, health). Ruff clean. `mypy --strict` clean on `app/retrieval`.
- `.pre-commit-config.yaml` added (ruff + scoped mypy), not yet installed as a git hook (`pre-commit install` still needs running locally).
- Next: Phase 2 — LangGraph pipeline (`app/graph/`: router, retrieve, grade_documents, rewrite_query, generate). This is the module that always gets a manual review regardless of author, per `AGENTS.md`.

## Phase 2 — LangGraph self-correcting RAG pipeline — 2026-07-04

Branch: `phase-2-langgraph` (stacked on `phase-1-backend-skeleton`, not yet merged to `main`).

- Deps: `langgraph` 1.2.7 + `langchain-anthropic` 1.4.8, resolved against the already-locked `langchain-core` 1.4.8 (v1 line). Added `pydantic.mypy` plugin so mypy strict understands `ChatAnthropic`'s pydantic-generated constructor.
- `app/graph/schemas.py` + `state.py` — `RouteDecision`/`GradeResult`/`ChunkRelevance`/`Source` structured-output models; `GraphState` TypedDict.
- `app/graph/llm.py` — `LLM` protocol (route/grade/rewrite_query/generate) + `AnthropicLLM`, using `.with_structured_output` for router/grader (structured output, not string parsing, per brief).
- `app/graph/deps.py` + `nodes.py` — `GraphDeps` DI container; the five nodes (router, retrieve, grade_documents, rewrite_query, generate), each logging name/duration/decision via structlog.
- `app/graph/build.py` — `StateGraph` wiring with the bounded rewrite loop; `build_default_graph()` (real deps) and `answer_question()` (single entry point for Phase 3/4 to reuse).
- Fixed a Phase 1 gap along the way: `OpenAIEmbedder` couldn't construct without a live `OPENAI_API_KEY` (blocked anything that builds default deps before keys are configured) — now falls back to a placeholder, matching `AnthropicLLM`'s pattern.
- **Manual review finding** (per `AGENTS.md` — this module always gets one): `generate()`'s empty-docs branch conflated "general route, no retrieval attempted" with "retrieval attempted but nothing relevant found," so the latter would falsely tell the user "no documents were needed" instead of "the docs didn't have the answer." Fixed by threading an explicit `retrieval_attempted` flag through `generate()`, with a dedicated prompt for the empty-but-attempted case and a regression test (`test_no_relevant_docs_still_marks_retrieval_as_attempted`).
- Rewrite-loop bound verified by hand and by test: `grade_documents_node` sets `limited_context` (the only place it's set) once `rewrite_count >= max_rewrites`; the routing function only reads it back. Loop can never exceed `max_rewrites` regardless of how many times the grader says "insufficient."
- 19 tests passing (11 Phase 1 + 8 graph). Ruff clean. `mypy --strict` clean on `app/graph` + `app/retrieval`. Mermaid export verified (`build_default_graph().get_graph().draw_mermaid()`) — diagram feeds the Phase 6 README.
- Next: Phase 3 — FastAPI `/documents` + `/chat` routes with SSE streaming, calling `app.graph.answer_question`.

## Phase 3 — FastAPI routes + SSE streaming — 2026-07-06

Branch: `phase-3-api` (stacked on `phase-2-langgraph`, not yet merged to `main`).

- **Streaming depth decision**: chose true token-level streaming over invoke-then-emit (brief only required the latter, but the frontend brief wants "streaming assistant responses"). This meant splitting the graph rather than just calling `answer_question`.
- `app/graph/build.py` — added `build_retrieval_graph(deps)`: reuses `_route_after_router`/`_decide_after_grade` unchanged, just remaps their `"generate"` outcome to `END` instead of a node, so it runs routing/retrieval/grading/rewrite and stops. `build_graph`/`answer_question` (Phase 2, non-streaming) are untouched and still there for Phase 4's MCP server.
- `app/graph/nodes.py` — extracted `select_cited_docs(state)` out of `generate_node` so the streaming path and the non-streaming path can't disagree on which chunks get cited.
- `app/graph/llm.py` — extracted `_build_generate_messages(...)` (the three-way general/no-relevant-docs/normal branch from Phase 2's review fix) so `generate()` and the new `stream_generate()` share it; `stream_generate` uses `ChatAnthropic.astream()`.
- `app/api/` (new package) — `dependencies.py` (`get_deps`/`get_retrieval_graph` reading `app.state`, overridden in tests via `app.dependency_overrides`), `routes_docs.py` (`POST/GET/DELETE /documents`, upload goes through a temp file into the existing Phase 1 loader/chunker), `routes_chat.py` (`POST /chat` — hand-rolled SSE, no new dependency: routing/retrieval/grading runs via `build_retrieval_graph`, then `stream_generate` tokens become `event: token` lines, a final `event: done` carries sources; mid-stream errors become `event: error` since HTTP headers are already committed by the time streaming starts).
- `app/main.py` — lifespan builds one real `GraphDeps` + retrieval graph on `app.state`; added `UnsupportedFileTypeError` → 400 and catch-all `Exception` → 500 handlers (structured JSON always, per brief — verified manually: uploading without `OPENAI_API_KEY` set returns a structured 500, not a bare traceback; `/chat` without keys degrades to an SSE `error` event).
- Small unrelated ruff config addition: exempted `fastapi.Depends` from the B008 "function call in default argument" rule — that's the standard FastAPI DI pattern, not the mutable-default bug the rule targets.
- 25 tests passing (19 from Phase 1+2 unchanged + 6 new API tests). Ruff clean. `mypy --strict` clean on `app/api` + `app/graph` + `app/retrieval`. Manually verified end-to-end against a running `uvicorn`: `/health`, upload, list, and both the success and no-API-key error paths for `/documents` and `/chat`.
- Next: Phase 4 — MCP server (`mcp-server/`) reusing `app.graph.build_graph`/`answer_question` (the full, non-streaming graph — MCP tools don't stream) and the ingestion/retrieval modules, per the brief's "shared package, not duplicated logic."

## Phase 4 — MCP server — 2026-07-06

Branch: `phase-4-mcp-server` (stacked on `phase-3-api`, not yet merged to `main`).

- **SDK version researched live** (not used before in this repo): stable `mcp` is 1.28.1 with `mcp.server.fastmcp.FastMCP` + `@mcp.tool()`. A `2.0.0b1` beta shipped 2026-06-30 renaming `FastMCP` → `MCPServer` — pinned `mcp[cli]>=1.27,<2` to stay on stable and avoid it.
- **Cross-package reuse decision**: `mcp-server/` is a separate uv "application" project (no `[build-system]`) with a plain path dependency on `../backend` (`{ path = "../backend" }`), not a uv workspace — keeps backend's own `.venv`/`uv.lock`/tooling from Phases 1-3 completely untouched. Confirmed `ask-my-docs-backend` resolves and installs from the local path (`uv pip show` points at `../backend`) rather than a duplicated copy of the logic.
- Needed a small Phase 1 fix along the way: added `backend/app/py.typed` (PEP 561 marker) — without it, mypy in `mcp-server` silently treated every `app.*` import as untyped `Any`, defeating type checking entirely for the one place this package is now consumed externally.
- `mcp-server/server.py` — one shared `GraphDeps` + `build_graph(deps)` built once at module load (not `build_default_graph()`, which would've meant a second independent `ChromaVectorStore`/`OpenAIEmbedder` pointed at the same persist dir). Three tools (`query_documents`, `add_document`, `list_documents`) are thin `@mcp.tool()` wrappers around plain `_query_documents`/`_add_document`/`_list_documents` functions — confirmed by inspection that `@mcp.tool()` actually returns the original function unchanged, but the indirection was worth keeping since it removes a test-time dependency on unconfirmed decorator behavior.
- Everything else is reused unchanged from `backend/app`: `graph.{GraphDeps, answer_question, build_graph}`, `graph.llm.AnthropicLLM`, `ingestion.{loader.load_document, chunker.chunk_text}`, `retrieval.{embedder.OpenAIEmbedder, store.ChromaVectorStore, store.new_document_id}`.
- `mcp-server/tests/fakes.py` re-declares a small `FakeLLM`/`FakeEmbedder` rather than importing `backend/tests/graph_fakes.py` — that file isn't part of the installed `ask-my-docs-backend` package (only `app` is), so it's a genuine package boundary, not avoidable duplication.
- 4 new tests passing, plus confirmed backend's own 25 tests/ruff/mypy are unaffected by the `py.typed` addition. Ruff and `mypy --strict` clean on `mcp-server`. Manually verified: `add_document` raises (doesn't silently no-op) on a missing path, an unsupported extension, and — without live API keys configured — a clean `AuthenticationError` at the embedding step rather than a crash.
- Next: Phase 5 — Next.js frontend (chat UI, streaming responses, source citation chips, document sidebar).
