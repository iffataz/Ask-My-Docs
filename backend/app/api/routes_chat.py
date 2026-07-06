import json
from collections.abc import AsyncIterator
from typing import Any, cast

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.api.dependencies import get_deps, get_retrieval_graph
from app.graph.deps import GraphDeps
from app.graph.nodes import select_cited_docs
from app.graph.schemas import Source
from app.graph.state import GraphState, initial_state
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


def sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _stream_answer(
    question: str,
    deps: GraphDeps,
    retrieval_graph: CompiledStateGraph[GraphState, None, GraphState, GraphState],
) -> AsyncIterator[str]:
    try:
        state = cast(GraphState, retrieval_graph.invoke(initial_state(question)))
        cited_docs = select_cited_docs(state)

        async for token in deps.llm.stream_generate(
            state["question"],
            cited_docs,
            limited_context=state["limited_context"],
            retrieval_attempted=state["route"] == "needs_retrieval",
        ):
            yield sse_event("token", {"text": token})

        sources = [Source(filename=d.filename, chunk_index=d.chunk_index) for d in cited_docs]
        yield sse_event("done", {"sources": [s.model_dump() for s in sources]})
    except Exception as exc:
        logger.error("chat_stream_failed", error=str(exc))
        yield sse_event("error", {"detail": "Failed to generate a response"})


@router.post("/chat")
async def chat(
    request: ChatRequest,
    deps: GraphDeps = Depends(get_deps),
    retrieval_graph: CompiledStateGraph[GraphState, None, GraphState, GraphState] = Depends(
        get_retrieval_graph
    ),
) -> StreamingResponse:
    return StreamingResponse(
        _stream_answer(request.question, deps, retrieval_graph),
        media_type="text/event-stream",
    )
