from app.config import get_settings
from app.graph.build import _decide_after_grade, build_graph
from app.graph.deps import GraphDeps
from app.graph.schemas import GradeResult
from app.graph.state import initial_state
from app.ingestion.chunker import Chunk
from app.retrieval.store import InMemoryVectorStore
from tests.graph_fakes import FakeEmbedder, FakeLLM


def _seed(vector_store: InMemoryVectorStore, embedder: FakeEmbedder) -> None:
    chunks = [Chunk(text="the sky is blue", source="doc.txt", chunk_index=0)]
    vector_store.add(
        document_id="doc1",
        filename="doc.txt",
        chunks=chunks,
        embeddings=embedder.embed_documents([c.text for c in chunks]),
    )


def test_sufficient_grade_skips_rewrite() -> None:
    embedder = FakeEmbedder()
    vector_store = InMemoryVectorStore()
    _seed(vector_store, embedder)
    llm = FakeLLM(sufficient_after=0)
    graph = build_graph(GraphDeps(llm=llm, embedder=embedder, vector_store=vector_store))

    result = graph.invoke(initial_state("what color is the sky"))

    assert llm.grade_calls == 1
    assert llm.rewrite_calls == 0
    assert result["rewrite_count"] == 0
    assert result["limited_context"] is False
    assert llm.generate_calls == 1


def test_rewrite_loop_is_bounded_at_max_rewrites() -> None:
    embedder = FakeEmbedder()
    vector_store = InMemoryVectorStore()
    _seed(vector_store, embedder)
    llm = FakeLLM(sufficient_after=None)  # never sufficient
    graph = build_graph(GraphDeps(llm=llm, embedder=embedder, vector_store=vector_store))
    max_rewrites = get_settings().max_rewrites

    result = graph.invoke(initial_state("what color is the sky"))

    assert llm.rewrite_calls == max_rewrites
    assert result["rewrite_count"] == max_rewrites
    assert llm.grade_calls == max_rewrites + 1
    assert result["limited_context"] is True
    assert llm.generate_calls == 1


def test_no_relevant_docs_still_marks_retrieval_as_attempted() -> None:
    """Regression: generate() must be able to tell "no documents were relevant" apart
    from "the general route never attempted retrieval" — both end up with an empty
    cited_docs list, but they need different answers (see app/graph/llm.py)."""
    embedder = FakeEmbedder()
    vector_store = InMemoryVectorStore()
    _seed(vector_store, embedder)
    llm = FakeLLM(sufficient_after=0, mark_relevant=False)
    graph = build_graph(GraphDeps(llm=llm, embedder=embedder, vector_store=vector_store))

    graph.invoke(initial_state("what color is the sky"))

    assert llm.last_generate_docs == []
    assert llm.last_retrieval_attempted is True


def test_decide_after_grade_routes_to_generate_when_sufficient() -> None:
    state = initial_state("q")
    state["relevance_grade"] = GradeResult(sufficient=True, relevances=[])
    state["limited_context"] = False

    assert _decide_after_grade(state) == "generate"


def test_decide_after_grade_routes_to_rewrite_when_insufficient_and_under_cap() -> None:
    state = initial_state("q")
    state["relevance_grade"] = GradeResult(sufficient=False, relevances=[])
    state["limited_context"] = False

    assert _decide_after_grade(state) == "rewrite_query"


def test_decide_after_grade_routes_to_generate_when_cap_reached() -> None:
    state = initial_state("q")
    state["relevance_grade"] = GradeResult(sufficient=False, relevances=[])
    state["rewrite_count"] = 2
    state["limited_context"] = True

    assert _decide_after_grade(state) == "generate"
