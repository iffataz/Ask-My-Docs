from collections.abc import AsyncIterator
from typing import Literal

from app.graph.schemas import ChunkRelevance, GradeResult, RouteDecision
from app.retrieval.store import ScoredChunk


class FakeEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        h = sum(ord(c) for c in text)
        return [float(h % 97), float(h % 31)]


class FakeLLM:
    def __init__(
        self,
        *,
        route: Literal["needs_retrieval", "general"] = "needs_retrieval",
        sufficient_after: int | None = 0,
        mark_relevant: bool = True,
    ) -> None:
        self._route = route
        self._sufficient_after = sufficient_after
        self._mark_relevant = mark_relevant
        self.grade_calls = 0

    def route(self, question: str) -> RouteDecision:
        return RouteDecision(route=self._route, reasoning="test")

    def grade(self, question: str, docs: list[ScoredChunk]) -> GradeResult:
        self.grade_calls += 1
        sufficient = (
            self._sufficient_after is not None and self.grade_calls > self._sufficient_after
        )
        relevances = [
            ChunkRelevance(chunk_index=i, relevant=self._mark_relevant) for i in range(len(docs))
        ]
        return GradeResult(sufficient=sufficient, relevances=relevances)

    def rewrite_query(self, original_question: str, current_question: str) -> str:
        return f"{original_question} (rewrite)"

    def generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> str:
        if not docs:
            return f"No relevant information found for: {question}"
        return f"Answer to '{question}' based on {len(docs)} chunk(s)"

    async def stream_generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> AsyncIterator[str]:
        for word in self.generate(
            question, docs, limited_context=limited_context, retrieval_attempted=retrieval_attempted
        ).split(" "):
            yield word + " "
