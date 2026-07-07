from dataclasses import dataclass

from app.graph.llm import LLM
from app.retrieval.embedder import Embedder
from app.retrieval.store import VectorStore


@dataclass(frozen=True)
class GraphDeps:
    llm: LLM
    embedder: Embedder
    vector_store: VectorStore
