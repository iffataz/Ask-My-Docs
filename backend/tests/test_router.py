from app.graph.build import build_graph
from app.graph.deps import GraphDeps
from app.graph.nodes import router_node
from app.graph.state import initial_state
from app.retrieval.store import InMemoryVectorStore
from tests.graph_fakes import FakeEmbedder, FakeLLM


def test_router_node_sets_route_from_llm_decision() -> None:
    deps = GraphDeps(
        llm=FakeLLM(route="general"),
        embedder=FakeEmbedder(),
        vector_store=InMemoryVectorStore(),
    )

    result = router_node(initial_state("hi there"), deps)

    assert result["route"] == "general"


def test_general_route_skips_retrieval_and_grading() -> None:
    llm = FakeLLM(route="general")
    vector_store = InMemoryVectorStore()
    deps = GraphDeps(llm=llm, embedder=FakeEmbedder(), vector_store=vector_store)
    graph = build_graph(deps)

    result = graph.invoke(initial_state("what's the weather like"))

    assert llm.grade_calls == 0
    assert llm.generate_calls == 1
    assert llm.last_generate_docs == []
    assert result["answer"] == "answer to: what's the weather like"
    assert result["sources"] == []
