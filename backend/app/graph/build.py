from functools import partial
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.deps import GraphDeps
from app.graph.llm import AnthropicLLM
from app.graph.nodes import (
    generate_node,
    grade_documents_node,
    retrieve_node,
    rewrite_query_node,
    router_node,
)
from app.graph.schemas import Source
from app.graph.state import GraphState, initial_state
from app.retrieval.embedder import OpenAIEmbedder
from app.retrieval.store import ChromaVectorStore


class AnswerResult:
    def __init__(self, answer: str, sources: list[Source]) -> None:
        self.answer = answer
        self.sources = sources


def _route_after_router(state: GraphState) -> Literal["retrieve", "generate"]:
    return "retrieve" if state["route"] == "needs_retrieval" else "generate"


def _decide_after_grade(state: GraphState) -> Literal["generate", "rewrite_query"]:
    grade = state["relevance_grade"]
    assert grade is not None
    if grade.sufficient or state["limited_context"]:
        return "generate"
    return "rewrite_query"


def build_graph(deps: GraphDeps) -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:
    graph = StateGraph(GraphState)

    graph.add_node("router", partial(router_node, deps=deps))
    graph.add_node("retrieve", partial(retrieve_node, deps=deps))
    graph.add_node("grade_documents", partial(grade_documents_node, deps=deps))
    graph.add_node("rewrite_query", partial(rewrite_query_node, deps=deps))
    graph.add_node("generate", partial(generate_node, deps=deps))

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router", _route_after_router, {"retrieve": "retrieve", "generate": "generate"}
    )
    graph.add_edge("retrieve", "grade_documents")
    graph.add_conditional_edges(
        "grade_documents",
        _decide_after_grade,
        {"generate": "generate", "rewrite_query": "rewrite_query"},
    )
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate", END)

    return graph.compile()


def build_default_graph() -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:
    deps = GraphDeps(
        llm=AnthropicLLM(),
        embedder=OpenAIEmbedder(),
        vector_store=ChromaVectorStore(),
    )
    return build_graph(deps)


def answer_question(
    question: str, graph: CompiledStateGraph[GraphState, None, GraphState, GraphState]
) -> AnswerResult:
    result = graph.invoke(initial_state(question))
    return AnswerResult(answer=result["answer"], sources=result["sources"])
