from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"

    chroma_persist_dir: str = "./.chroma"

    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_k: int = 5
    max_rewrites: int = 2

    cors_origins: list[str] = ["http://localhost:3000"]
    log_json: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
