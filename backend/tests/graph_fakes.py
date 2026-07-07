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
        """sufficient_after: grade() returns sufficient=True once it has been called
        more than this many times. None means never sufficient (always insufficient).
        mark_relevant: whether grade() marks retrieved chunks as relevant.
        """
        self._route = route
        self._sufficient_after = sufficient_after
        self._mark_relevant = mark_relevant
        self.grade_calls = 0
        self.rewrite_calls = 0
        self.generate_calls = 0
        self.last_generate_docs: list[ScoredChunk] = []
        self.last_limited_context = False
        self.last_retrieval_attempted = False

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
        self.rewrite_calls += 1
        return f"{original_question} (rewrite {self.rewrite_calls})"

    def generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> str:
        self.generate_calls += 1
        self.last_generate_docs = docs
        self.last_limited_context = limited_context
        self.last_retrieval_attempted = retrieval_attempted
        return f"answer to: {question}"
