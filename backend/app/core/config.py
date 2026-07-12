"""
Centralized application configuration via pydantic-settings.

This is the ONLY module that should read environment variables directly;
all other modules must obtain configuration through the `settings` object
defined here. See PLAN.md Section 8, TASKS.md T03, and backend.mdc.
"""

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    # Required: the app cannot serve grounded answers without a real Gemini
    # key, so a missing/blank value must fail loudly at startup rather than
    # silently falling back to an empty string (see general.mdc, TASKS.md T03).
    google_api_key: SecretStr = Field(
        ...,
        description="Gemini API key (required). Set in a .env file - see .env.example.",
    )
    gemini_model: str = "gemini-2.5-flash"

    # Auth
    backend_api_tokens: str = ""

    # Embeddings
    embedding_model: str = "BAAI/bge-base-en-v1.5"

    # Retrieval
    enable_reranker: bool = False
    retrieval_top_k: int = 20
    rerank_top_n: int = 5
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Hybrid retrieval fusion weights (semantic vs. keyword leg). Must sum to
    # a positive total; EnsembleRetriever normalizes internally either way.
    hybrid_semantic_weight: float = 0.5
    hybrid_keyword_weight: float = 0.5

    # Confidence thresholds
    confidence_refusal_threshold: float = 0.4
    confidence_caution_threshold: float = 0.6

    # Storage
    sqlite_db_path: str = "./data/app.db"
    faiss_index_dir: str = "./data/faiss_index"
    bm25_index_dir: str = "./data/bm25_index"

    # Cache / rate limiting
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 30

    @field_validator("google_api_key")
    @classmethod
    def _google_api_key_must_not_be_blank(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError(
                "GOOGLE_API_KEY must not be blank - set it in your .env file (see .env.example)"
            )
        return value


# TODO: wrap in an lru_cache-based get_settings() factory once wired into
# routes/dependencies, so tests can override settings cleanly.
settings = Settings()
