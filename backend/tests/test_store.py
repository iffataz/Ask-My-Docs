from app.ingestion.chunker import Chunk
from app.retrieval.store import InMemoryVectorStore


def _chunk(text: str, index: int) -> Chunk:
    return Chunk(text=text, source="doc.txt", chunk_index=index)


def test_similarity_search_returns_nearest_first() -> None:
    store = InMemoryVectorStore()
    store.add(
        document_id="doc1",
        filename="doc.txt",
        chunks=[_chunk("a", 0), _chunk("b", 1)],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    results = store.similarity_search([1.0, 0.0], k=2)

    assert results[0].text == "a"
    assert results[0].score > results[1].score


def test_k_bounds_results() -> None:
    store = InMemoryVectorStore()
    store.add(
        document_id="doc1",
        filename="doc.txt",
        chunks=[_chunk("a", 0), _chunk("b", 1), _chunk("c", 2)],
        embeddings=[[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]],
    )

    results = store.similarity_search([1.0, 0.0], k=2)

    assert len(results) == 2


def test_delete_removes_document() -> None:
    store = InMemoryVectorStore()
    store.add(
        document_id="doc1",
        filename="doc.txt",
        chunks=[_chunk("a", 0)],
        embeddings=[[1.0, 0.0]],
    )
    store.add(
        document_id="doc2",
        filename="other.txt",
        chunks=[_chunk("b", 0)],
        embeddings=[[0.0, 1.0]],
    )

    store.delete("doc1")
    results = store.similarity_search([1.0, 0.0], k=10)

    assert all(r.document_id != "doc1" for r in results)
    assert len(results) == 1


def test_list_documents_reports_chunk_counts() -> None:
    store = InMemoryVectorStore()
    store.add(
        document_id="doc1",
        filename="doc.txt",
        chunks=[_chunk("a", 0), _chunk("b", 1)],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    docs = store.list_documents()

    assert len(docs) == 1
    assert docs[0].document_id == "doc1"
    assert docs[0].filename == "doc.txt"
    assert docs[0].chunk_count == 2
