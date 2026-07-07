import math
import uuid
from abc import ABC, abstractmethod

import chromadb
from pydantic import BaseModel

from app.config import get_settings
from app.ingestion.chunker import Chunk


class ScoredChunk(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    text: str
    score: float


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class VectorStore(ABC):
    @abstractmethod
    def add(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None: ...

    @abstractmethod
    def similarity_search(self, query_embedding: list[float], k: int) -> list[ScoredChunk]: ...

    @abstractmethod
    def list_documents(self) -> list[DocumentInfo]: ...

    @abstractmethod
    def delete(self, document_id: str) -> None: ...


class ChromaVectorStore(VectorStore):
    COLLECTION_NAME = "documents"

    def __init__(self, *, persist_dir: str | None = None) -> None:
        settings = get_settings()
        client = chromadb.PersistentClient(path=persist_dir or settings.chroma_persist_dir)
        self._collection = client.get_or_create_collection(self.COLLECTION_NAME)

    def add(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        if not chunks:
            return
        self._collection.add(
            ids=[f"{document_id}:{c.chunk_index}" for c in chunks],
            embeddings=embeddings,  # type: ignore[arg-type]  # chromadb stubs don't accept plain list[list[float]]
            documents=[c.text for c in chunks],
            metadatas=[
                {"document_id": document_id, "filename": filename, "chunk_index": c.chunk_index}
                for c in chunks
            ],
        )

    def similarity_search(self, query_embedding: list[float], k: int) -> list[ScoredChunk]:
        result = self._collection.query(
            query_embeddings=[query_embedding],  # type: ignore[arg-type]
            n_results=k,
        )

        documents = (result["documents"] or [[]])[0]
        metadatas = (result["metadatas"] or [[]])[0]
        distances = (result["distances"] or [[]])[0]

        return [
            ScoredChunk(
                document_id=str(meta["document_id"]),
                filename=str(meta["filename"]),
                chunk_index=int(meta["chunk_index"]),  # type: ignore[arg-type]  # we control this metadata's shape
                text=doc,
                score=1.0 - distance,
            )
            for doc, meta, distance in zip(documents, metadatas, distances, strict=True)
        ]

    def list_documents(self) -> list[DocumentInfo]:
        result = self._collection.get()
        counts: dict[str, DocumentInfo] = {}
        for meta in result["metadatas"] or []:
            document_id = str(meta["document_id"])
            if document_id not in counts:
                counts[document_id] = DocumentInfo(
                    document_id=document_id, filename=str(meta["filename"]), chunk_count=0
                )
            counts[document_id].chunk_count += 1
        return list(counts.values())

    def delete(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._chunks: dict[str, list[tuple[str, Chunk, list[float]]]] = {}
        self._filenames: dict[str, str] = {}

    def add(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        self._filenames[document_id] = filename
        entries = self._chunks.setdefault(document_id, [])
        entries.extend(zip([document_id] * len(chunks), chunks, embeddings, strict=True))

    def similarity_search(self, query_embedding: list[float], k: int) -> list[ScoredChunk]:
        scored: list[ScoredChunk] = []
        for document_id, entries in self._chunks.items():
            for _, chunk, embedding in entries:
                scored.append(
                    ScoredChunk(
                        document_id=document_id,
                        filename=self._filenames[document_id],
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        score=_cosine_similarity(query_embedding, embedding),
                    )
                )
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]

    def list_documents(self) -> list[DocumentInfo]:
        return [
            DocumentInfo(
                document_id=document_id,
                filename=self._filenames[document_id],
                chunk_count=len(entries),
            )
            for document_id, entries in self._chunks.items()
        ]

    def delete(self, document_id: str) -> None:
        self._chunks.pop(document_id, None)
        self._filenames.pop(document_id, None)


def new_document_id() -> str:
    return uuid.uuid4().hex


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
