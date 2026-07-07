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
