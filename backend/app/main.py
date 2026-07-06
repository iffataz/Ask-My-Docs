from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_chat, routes_docs
from app.config import get_settings
from app.graph.build import build_retrieval_graph
from app.graph.deps import GraphDeps
from app.graph.llm import AnthropicLLM
from app.ingestion.loader import UnsupportedFileTypeError
from app.logging import configure_logging, get_logger
from app.retrieval.embedder import OpenAIEmbedder
from app.retrieval.store import ChromaVectorStore

configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    deps = GraphDeps(
        llm=AnthropicLLM(), embedder=OpenAIEmbedder(), vector_store=ChromaVectorStore()
    )
    app.state.deps = deps
    app.state.retrieval_graph = build_retrieval_graph(deps)
    logger.info("app_startup")
    yield


app = FastAPI(title="Ask My Docs", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_docs.router)
app.include_router(routes_chat.router)


@app.exception_handler(UnsupportedFileTypeError)
async def handle_unsupported_file_type(_: Request, exc: UnsupportedFileTypeError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
