from pathlib import Path

import pytest
from app.graph.build import build_graph
from app.graph.deps import GraphDeps
from app.retrieval.store import InMemoryVectorStore

import server
from tests.fakes import FakeEmbedder, FakeLLM


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch, *, llm: FakeLLM | None = None
) -> GraphDeps:
    deps = GraphDeps(
        llm=llm or FakeLLM(), embedder=FakeEmbedder(), vector_store=InMemoryVectorStore()
    )
    monkeypatch.setattr(server, "_deps", deps)
    monkeypatch.setattr(server, "_graph", build_graph(deps))
    return deps


def test_add_document_reports_chunk_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fakes(monkeypatch)
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello world")

    result = server._add_document(str(file_path))

    assert "note.txt" in result
    assert "1 chunks" in result


def test_list_documents_after_add(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch)
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello world")
    server._add_document(str(file_path))

    docs = server._list_documents()

    assert len(docs) == 1
    assert docs[0]["filename"] == "note.txt"


def test_query_documents_includes_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fakes(monkeypatch, llm=FakeLLM(sufficient_after=0))
    file_path = tmp_path / "note.txt"
    file_path.write_text("the sky is blue")
    server._add_document(str(file_path))

    answer = server._query_documents("what color is the sky")

    assert "Sources:" in answer
    assert "note.txt" in answer


def test_query_documents_with_no_relevant_docs_still_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fakes(monkeypatch, llm=FakeLLM(sufficient_after=None, mark_relevant=False))
    file_path = tmp_path / "note.txt"
    file_path.write_text("the sky is blue")
    server._add_document(str(file_path))

    answer = server._query_documents("what color is the sky")

    assert answer
    assert "Sources:" not in answer
