from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"

    chroma_persist_dir: str = "./.chroma"

    # Measured in characters (RecursiveCharacterTextSplitter's unit), not tokens:
    # 3200 chars ≈ the brief's ~800 tokens. Too-small chunks shred section
    # headings away from their tables and wreck retrieval on structured docs.
    chunk_size: int = 3200
    chunk_overlap: int = 600
    retrieval_k: int = 5
    max_rewrites: int = 2

    cors_origins: list[str] = ["http://localhost:3000"]
    log_json: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
