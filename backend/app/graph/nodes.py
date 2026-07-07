import time
from typing import Any

from app.config import get_settings
from app.graph.deps import GraphDeps
from app.graph.schemas import Source
from app.graph.state import GraphState
from app.logging import get_logger

logger = get_logger(__name__)


def _log_transition(node: str, start: float, **fields: Any) -> None:
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info("graph_node", node=node, duration_ms=duration_ms, **fields)


def router_node(state: GraphState, deps: GraphDeps) -> dict[str, Any]:
    start = time.perf_counter()
    decision = deps.llm.route(state["question"])
    _log_transition("router", start, route=decision.route)
    return {"route": decision.route}


def retrieve_node(state: GraphState, deps: GraphDeps) -> dict[str, Any]:
    start = time.perf_counter()
    settings = get_settings()
    query_embedding = deps.embedder.embed_query(state["question"])
    docs = deps.vector_store.similarity_search(query_embedding, k=settings.retrieval_k)
    _log_transition("retrieve", start, num_docs=len(docs))
    return {"retrieved_docs": docs}


def grade_documents_node(state: GraphState, deps: GraphDeps) -> dict[str, Any]:
    start = time.perf_counter()
    settings = get_settings()
    grade = deps.llm.grade(state["question"], state["retrieved_docs"])

    # The rewrite cap is decided here (not in the routing function) so it's the single
    # place that sets limited_context; decide_after_grade only reads it back from state.
    rewrite_cap_reached = state["rewrite_count"] >= settings.max_rewrites
    limited_context = (not grade.sufficient) and rewrite_cap_reached

    _log_transition(
        "grade_documents", start, sufficient=grade.sufficient, limited_context=limited_context
    )
    return {"relevance_grade": grade, "limited_context": limited_context}


def rewrite_query_node(state: GraphState, deps: GraphDeps) -> dict[str, Any]:
    start = time.perf_counter()
    new_question = deps.llm.rewrite_query(state["original_question"], state["question"])
    new_count = state["rewrite_count"] + 1
    _log_transition("rewrite_query", start, rewrite_count=new_count)
    return {"question": new_question, "rewrite_count": new_count}


def generate_node(state: GraphState, deps: GraphDeps) -> dict[str, Any]:
    start = time.perf_counter()
    grade = state["relevance_grade"]
    docs = state["retrieved_docs"]

    if grade is not None:
        # ChunkRelevance.chunk_index is the position of the doc in `docs` (0-based, as
        # presented to the grader), not the document's own chunk_index — map back by position.
        relevant_positions = {r.chunk_index for r in grade.relevances if r.relevant}
        cited_docs = [doc for i, doc in enumerate(docs) if i in relevant_positions]
    else:
        cited_docs = docs

    answer = deps.llm.generate(
        state["question"],
        cited_docs,
        limited_context=state["limited_context"],
        retrieval_attempted=state["route"] == "needs_retrieval",
    )
    sources = [Source(filename=d.filename, chunk_index=d.chunk_index) for d in cited_docs]

    _log_transition("generate", start, limited_context=state["limited_context"])
    return {"answer": answer, "sources": sources}
