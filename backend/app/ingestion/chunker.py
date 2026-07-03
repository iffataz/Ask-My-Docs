from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from app.config import get_settings


class Chunk(BaseModel):
    text: str
    source: str
    chunk_index: int


def chunk_text(
    text: str,
    *,
    source: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    if not text.strip():
        return []

    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
    )

    return [
        Chunk(text=piece, source=source, chunk_index=i)
        for i, piece in enumerate(splitter.split_text(text))
    ]
