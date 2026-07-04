from typing import Protocol

from openai import OpenAI

from app.config import get_settings


class Embedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class OpenAIEmbedder:
    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        settings = get_settings()
        self._model = model or settings.embedding_model
        # OpenAI's client treats "" same as missing and raises at construction, so fall
        # back to a placeholder (not None/"") so construction succeeds without a live
        # key; the actual auth error surfaces at request time, matching Settings'
        # "optional at construction" design (see app/config.py).
        self._client = OpenAI(api_key=api_key or settings.openai_api_key or "unset")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
