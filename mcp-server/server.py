from typing import Any

from app.graph import GraphDeps, answer_question, build_graph
from app.graph.llm import AnthropicLLM
from app.ingestion.chunker import chunk_text
from app.ingestion.loader import load_document
from app.retrieval.embedder import OpenAIEmbedder
from app.retrieval.store import ChromaVectorStore, new_document_id
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Ask My Docs")

_deps = GraphDeps(llm=AnthropicLLM(), embedder=OpenAIEmbedder(), vector_store=ChromaVectorStore())
_graph = build_graph(_deps)


def _query_documents(question: str) -> str:
    result = answer_question(question, _graph)
    if not result.sources:
        return result.answer
    citations = "; ".join(f"{s.filename} (chunk {s.chunk_index})" for s in result.sources)
    return f"{result.answer}\n\nSources: {citations}"


def _add_document(path: str) -> str:
    loaded = load_document(path)
    chunks = chunk_text(loaded.text, source=loaded.filename)
    embeddings = _deps.embedder.embed_documents([c.text for c in chunks])
    document_id = new_document_id()
    _deps.vector_store.add(
        document_id=document_id, filename=loaded.filename, chunks=chunks, embeddings=embeddings
    )
    return f"Ingested {loaded.filename}: {len(chunks)} chunks (document_id={document_id})"


def _list_documents() -> list[dict[str, Any]]:
    return [d.model_dump() for d in _deps.vector_store.list_documents()]


@mcp.tool()
def query_documents(question: str) -> str:
    """Answer a question using the indexed documents, with source citations."""
    return _query_documents(question)


@mcp.tool()
def add_document(path: str) -> str:
    """Ingest a local file (pdf, md, or txt) into the document index."""
    return _add_document(path)


@mcp.tool()
def list_documents() -> list[dict[str, Any]]:
    """List indexed documents with their chunk counts."""
    return _list_documents()


if __name__ == "__main__":
    mcp.run(transport="stdio")
