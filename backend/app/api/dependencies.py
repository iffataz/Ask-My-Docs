from fastapi import Request
from langgraph.graph.state import CompiledStateGraph

from app.graph.deps import GraphDeps
from app.graph.state import GraphState


def get_deps(request: Request) -> GraphDeps:
    deps: GraphDeps = request.app.state.deps
    return deps


def get_retrieval_graph(
    request: Request,
) -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:
    graph: CompiledStateGraph[GraphState, None, GraphState, GraphState] = (
        request.app.state.retrieval_graph
    )
    return graph
