from collections.abc import Iterator
from typing import NamedTuple

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_deps, get_retrieval_graph
from app.graph.build import build_retrieval_graph
from app.graph.deps import GraphDeps
from app.main import app
from app.retrieval.store import InMemoryVectorStore
from tests.graph_fakes import FakeEmbedder, FakeLLM


class FakeAppContext(NamedTuple):
    client: TestClient
    deps: GraphDeps
    llm: FakeLLM


@pytest.fixture
def fake_app() -> Iterator[FakeAppContext]:
    llm = FakeLLM()
    deps = GraphDeps(llm=llm, embedder=FakeEmbedder(), vector_store=InMemoryVectorStore())

    app.dependency_overrides[get_deps] = lambda: deps
    app.dependency_overrides[get_retrieval_graph] = lambda: build_retrieval_graph(deps)

    yield FakeAppContext(client=TestClient(app), deps=deps, llm=llm)

    app.dependency_overrides.clear()
