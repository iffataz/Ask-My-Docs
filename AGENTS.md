# Agent Workflow

This project is built in the 6 phases defined in [ask-my-docs-brief.md](ask-my-docs-brief.md#build-order):

1. Backend skeleton (config, ingestion, vector store, chunker tests)
2. LangGraph pipeline (`backend/app/graph/`) with tests
3. FastAPI routes + SSE streaming
4. MCP server reusing the graph
5. Frontend
6. Docker compose, README polish, Mermaid graph export

## Per-phase loop

For each phase:

1. **Plan mode** — enter plan mode, propose the implementation plan for that phase only.
2. **User accepts** the plan (or sends it back for revision).
3. **Execute** — Sonnet implements the accepted plan directly (no subagent dispatch needed for straightforward phases).
4. **Review** — before moving to the next phase, review the diff for the phase. `backend/app/graph/` (router, retrieve, grade_documents, rewrite_query, generate, and the StateGraph wiring in `build.py`) gets a careful manual review every time it changes, regardless of which model wrote it — it's the core of the project and the place where bugs (unbounded rewrite loops, bad conditional edges, wrong state typing) are least likely to surface via type checking alone.
5. **Update [MEMORY.md](MEMORY.md)** with what shipped, what's outstanding, and any decisions made.
6. Commit in logical increments (conventional commits), not one mega-commit per phase.

## When to use subagents

Dispatch a subagent (via the `Explore` or `general-purpose` agent) instead of doing it inline when:
- Researching a LangGraph/MCP SDK API question that would otherwise burn several tool calls
- Running an independent, well-scoped chunk of a phase in parallel with another (e.g., writing chunker tests while the vector store interface is being reviewed)

Do not dispatch a subagent for the graph module implementation itself — write and review that directly so the review step in step 4 is meaningful.
