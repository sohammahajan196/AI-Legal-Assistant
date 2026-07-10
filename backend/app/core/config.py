"""
Centralized application configuration via pydantic-settings.

This is the ONLY module that should read environment variables directly;
all other modules must obtain configuration through the `settings` object
defined here. See PLAN.md Section 8, TASKS.md T03, and backend.mdc.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Auth
    backend_api_tokens: str = ""

    # Embeddings
    embedding_model: str = "BAAI/bge-base-en-v1.5"

    # Retrieval
    enable_reranker: bool = False
    retrieval_top_k: int = 20
    rerank_top_n: int = 5

    # Confidence thresholds
    confidence_refusal_threshold: float = 0.4
    confidence_caution_threshold: float = 0.6

    # Storage
    sqlite_db_path: str = "./data/app.db"
    faiss_index_dir: str = "./data/faiss_index"

    # Cache / rate limiting
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 30


# TODO: wrap in an lru_cache-based get_settings() factory once wired into
# routes/dependencies, so tests can override settings cleanly.
settings = Settings()
