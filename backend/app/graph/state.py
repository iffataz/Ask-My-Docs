from typing import TypedDict

from app.graph.schemas import GradeResult, Source
from app.retrieval.store import ScoredChunk


class GraphState(TypedDict):
    question: str
    original_question: str
    route: str
    retrieved_docs: list[ScoredChunk]
    relevance_grade: GradeResult | None
    rewrite_count: int
    limited_context: bool
    answer: str
    sources: list[Source]


def initial_state(question: str) -> GraphState:
    return GraphState(
        question=question,
        original_question=question,
        route="",
        retrieved_docs=[],
        relevance_grade=None,
        rewrite_count=0,
        limited_context=False,
        answer="",
        sources=[],
    )
