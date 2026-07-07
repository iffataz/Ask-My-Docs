# Backend

RAG backend for Ask My Docs — FastAPI + LangGraph (graph pipeline added in Phase 2).

## Setup

```bash
# install uv: https://docs.astral.sh/uv/getting-started/installation/
cd backend
uv sync
cp ../.env.example ../.env   # fill in ANTHROPIC_API_KEY / OPENAI_API_KEY
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
curl localhost:8000/health
```

## Test / lint / typecheck

```bash
uv run pytest -q
uv run ruff check .
uv run mypy app/retrieval
```
