# MCP Server

Exposes Ask My Docs' RAG pipeline as MCP tools (stdio transport), reusing `backend/app`'s graph, ingestion, and retrieval modules directly — no duplicated logic.

## Tools

- `query_documents(question: str) -> str` — runs the full LangGraph pipeline, returns the answer with a `Sources:` line when documents were cited.
- `add_document(path: str) -> str` — ingests a local file (pdf/md/txt) into the shared document index.
- `list_documents() -> list` — lists indexed documents with chunk counts.

## Setup

```bash
cd mcp-server
uv sync
cp ../.env.example ../.env   # fill in ANTHROPIC_API_KEY / OPENAI_API_KEY
```

`ask-my-docs-backend` is pulled in as a local path dependency on `../backend` — no separate install step needed for it.

## Run standalone

```bash
uv run server.py
```

## Claude Desktop setup

Add to `claude_desktop_config.json` (find it via Claude Desktop's Settings → Developer):

```json
{
  "mcpServers": {
    "ask-my-docs": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/ask-my-docs/mcp-server", "run", "server.py"]
    }
  }
}
```

Restart Claude Desktop, then look for "ask-my-docs" under the 🔌 tools icon.

## Demo

1. Ask Claude: "Add the document at `/path/to/some/file.txt`" — it calls `add_document`.
2. Ask a question about that file's content — Claude calls `query_documents` and answers with citations.
3. Ask "What documents do I have indexed?" — Claude calls `list_documents`.

## Test / lint / typecheck

```bash
uv run pytest -q
uv run ruff check .
uv run mypy .
```
