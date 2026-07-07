import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.dependencies import get_deps
from app.graph.deps import GraphDeps
from app.ingestion.chunker import chunk_text
from app.ingestion.loader import load_document
from app.retrieval.store import DocumentInfo, new_document_id

router = APIRouter()


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class DeleteResponse(BaseModel):
    document_id: str


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile, deps: GraphDeps = Depends(get_deps)
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file is missing a filename")

    suffix = Path(file.filename).suffix
    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        loaded = load_document(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    chunks = chunk_text(loaded.text, source=file.filename)
    embeddings = deps.embedder.embed_documents([c.text for c in chunks])
    document_id = new_document_id()
    deps.vector_store.add(
        document_id=document_id, filename=file.filename, chunks=chunks, embeddings=embeddings
    )

    return DocumentUploadResponse(
        document_id=document_id, filename=file.filename, chunk_count=len(chunks)
    )


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(deps: GraphDeps = Depends(get_deps)) -> list[DocumentInfo]:
    return deps.vector_store.list_documents()


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str, deps: GraphDeps = Depends(get_deps)
) -> DeleteResponse:
    deps.vector_store.delete(document_id)
    return DeleteResponse(document_id=document_id)
