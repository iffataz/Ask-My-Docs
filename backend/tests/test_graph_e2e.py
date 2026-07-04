from app.graph.build import answer_question, build_graph
from app.graph.deps import GraphDeps
from app.ingestion.chunker import Chunk
from app.retrieval.store import InMemoryVectorStore
from tests.graph_fakes import FakeEmbedder, FakeLLM


def test_end_to_end_answer_includes_sources() -> None:
    embedder = FakeEmbedder()
    vector_store = InMemoryVectorStore()
    chunks = [
        Chunk(text="Ask My Docs is a RAG app.", source="readme.md", chunk_index=0),
        Chunk(text="It uses LangGraph for orchestration.", source="readme.md", chunk_index=1),
    ]
    vector_store.add(
        document_id="doc1",
        filename="readme.md",
        chunks=chunks,
        embeddings=embedder.embed_documents([c.text for c in chunks]),
    )
    llm = FakeLLM(route="needs_retrieval", sufficient_after=0)
    graph = build_graph(GraphDeps(llm=llm, embedder=embedder, vector_store=vector_store))

    result = answer_question("What does Ask My Docs use for orchestration?", graph)

    assert result.answer.startswith("answer to:")
    assert len(result.sources) > 0
    assert all(s.filename == "readme.md" for s in result.sources)
    assert {s.chunk_index for s in result.sources} <= {0, 1}
