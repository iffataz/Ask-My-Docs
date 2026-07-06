from collections.abc import AsyncIterator
from typing import Protocol

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.config import get_settings
from app.graph.schemas import GradeResult, RouteDecision
from app.retrieval.store import ScoredChunk

ROUTER_SYSTEM_PROMPT = (
    "You classify a user's question for a document Q&A assistant. "
    "Respond with route='needs_retrieval' if answering requires looking up the user's "
    "uploaded documents. Respond with route='general' for greetings, small talk, or "
    "questions clearly unrelated to any documents (e.g. general knowledge, math, coding help "
    "that doesn't reference 'the docs')."
)

GRADE_SYSTEM_PROMPT = (
    "You grade whether retrieved document chunks are sufficient to answer a question. "
    "For each chunk (identified by its position, starting at 0), decide if it is relevant "
    "to the question. Set sufficient=true only if the relevant chunks together contain "
    "enough information to answer the question well."
)

REWRITE_SYSTEM_PROMPT = (
    "The previous search query did not retrieve sufficient context. Rewrite the question "
    "to improve retrieval — use different phrasing or more specific/alternate terms while "
    "preserving the original intent. Respond with only the rewritten question, no preamble."
)

GENERATE_SYSTEM_PROMPT = (
    "Answer the user's question grounded only in the provided document chunks. "
    "Cite sources inline as (filename, chunk N) after claims drawn from a chunk. "
    "If the context is marked as limited, explicitly tell the user the retrieved context "
    "may be insufficient rather than presenting the answer as complete or filling gaps "
    "with your own knowledge. Never fabricate information not present in the chunks."
)

GENERAL_SYSTEM_PROMPT = (
    "Answer the user's question directly and mention that no documents were consulted, "
    "since this question did not require document lookup."
)

NO_RELEVANT_DOCS_SYSTEM_PROMPT = (
    "The user's question required looking up their documents, but no relevant information "
    "was found after searching. Tell the user the documents don't contain enough information "
    "to answer this question — do not answer from your own general knowledge instead."
)


def _format_docs(docs: list[ScoredChunk]) -> str:
    return "\n\n".join(
        f"[{i}] (source: {doc.filename}, chunk {doc.chunk_index})\n{doc.text}"
        for i, doc in enumerate(docs)
    )


def _build_generate_messages(
    question: str,
    docs: list[ScoredChunk],
    *,
    limited_context: bool,
    retrieval_attempted: bool,
) -> list[BaseMessage]:
    if not retrieval_attempted:
        return [SystemMessage(content=GENERAL_SYSTEM_PROMPT), HumanMessage(content=question)]

    if not docs:
        return [
            SystemMessage(content=NO_RELEVANT_DOCS_SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]

    context_note = (
        "\n\n(Note: context is limited — say so in the answer.)" if limited_context else ""
    )
    prompt = f"Question: {question}\n\nDocument chunks:\n{_format_docs(docs)}{context_note}"
    return [SystemMessage(content=GENERATE_SYSTEM_PROMPT), HumanMessage(content=prompt)]


class LLM(Protocol):
    def route(self, question: str) -> RouteDecision: ...

    def grade(self, question: str, docs: list[ScoredChunk]) -> GradeResult: ...

    def rewrite_query(self, original_question: str, current_question: str) -> str: ...

    def generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> str: ...

    def stream_generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> AsyncIterator[str]: ...


class AnthropicLLM:
    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        settings = get_settings()
        self._chat = ChatAnthropic(
            model=model or settings.anthropic_model,
            # empty string (not None) so construction succeeds without a live key;
            # the actual auth error surfaces at .invoke() time, matching Settings'
            # "optional at construction" design (see app/config.py).
            anthropic_api_key=api_key or settings.anthropic_api_key or "",
        )

    def route(self, question: str) -> RouteDecision:
        structured = self._chat.with_structured_output(RouteDecision)
        result = structured.invoke(
            [SystemMessage(content=ROUTER_SYSTEM_PROMPT), HumanMessage(content=question)]
        )
        assert isinstance(result, RouteDecision)
        return result

    def grade(self, question: str, docs: list[ScoredChunk]) -> GradeResult:
        if not docs:
            return GradeResult(sufficient=False, relevances=[])

        structured = self._chat.with_structured_output(GradeResult)
        prompt = f"Question: {question}\n\nRetrieved chunks:\n{_format_docs(docs)}"
        result = structured.invoke(
            [SystemMessage(content=GRADE_SYSTEM_PROMPT), HumanMessage(content=prompt)]
        )
        assert isinstance(result, GradeResult)
        return result

    def rewrite_query(self, original_question: str, current_question: str) -> str:
        prompt = f"Original question: {original_question}\nLast search query: {current_question}"
        result = self._chat.invoke(
            [SystemMessage(content=REWRITE_SYSTEM_PROMPT), HumanMessage(content=prompt)]
        )
        return str(result.content)

    def generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> str:
        messages = _build_generate_messages(
            question, docs, limited_context=limited_context, retrieval_attempted=retrieval_attempted
        )
        result = self._chat.invoke(messages)
        return str(result.content)

    async def stream_generate(
        self,
        question: str,
        docs: list[ScoredChunk],
        *,
        limited_context: bool,
        retrieval_attempted: bool,
    ) -> AsyncIterator[str]:
        messages = _build_generate_messages(
            question, docs, limited_context=limited_context, retrieval_attempted=retrieval_attempted
        )
        async for chunk in self._chat.astream(messages):
            if chunk.content:
                yield str(chunk.content)
