"""
Centralized application configuration via pydantic-settings.

This is the ONLY module that should read environment variables directly;
all other modules must obtain configuration through the `settings` object
defined here. See PLAN.md Section 8, TASKS.md T03, and backend.mdc.
"""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py → parents[2] == backend/, parents[3] == repo root.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent


def default_env_files() -> tuple[Path, ...]:
    """Absolute ``.env`` paths, independent of the process working directory.

    Loads the repo-root ``.env`` first, then ``backend/.env``. Later files
    override earlier ones; real process env vars still win over both.
    Missing files are ignored by pydantic-settings.
    """
    return (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables / a .env file."""

    model_config = SettingsConfigDict(
        env_file=default_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    # Required: the app cannot serve grounded answers without a real Gemini
    # key, so a missing/blank value must fail loudly at startup rather than
    # silently falling back to an empty string (see general.mdc, TASKS.md T03).
    google_api_key: SecretStr = Field(
        ...,
        description="Gemini API key (required). Set in a .env file - see .env.example.",
    )
    # Default must stay on a model available to new Gemini API keys.
    # gemini-2.5-flash returns 404 NOT_FOUND for new users (migrate to 3.5).
    gemini_model: str = "gemini-3.5-flash"
    gemini_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for Gemini generation (0 = deterministic).",
    )
    gemini_max_retries: int = Field(
        default=4,
        ge=0,
        le=10,
        description=(
            "Max retry attempts on Gemini 503/UNAVAILABLE (exponential backoff "
            "with jitter; 4 => up to 5 total attempts including the first call)."
        ),
    )
    gemini_retry_base_delay_seconds: float = Field(
        default=1.0,
        gt=0.0,
        le=60.0,
        description="Base delay (seconds) for Gemini retry backoff: 1s, 2s, 4s, 8s, …",
    )
    gemini_fallback_model: str = Field(
        default="",
        description=(
            "Optional secondary Gemini model (e.g. gemini-2.5-flash). When set, "
            "used after the primary model exhausts retries on 503/UNAVAILABLE."
        ),
    )

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

    # Confidence score weights (retrieval_component vs. groundedness_component,
    # see PLAN.md Section 7 and app/rag/confidence.py). Named w1/w2 there.
    confidence_retrieval_weight: float = 0.5
    confidence_groundedness_weight: float = 0.5

    # Storage
    sqlite_db_path: str = "./data/app.db"
    faiss_index_dir: str = "./data/faiss_index"
    bm25_index_dir: str = "./data/bm25_index"

    # Cache / rate limiting
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=1,
        description="TTL in seconds for cached LegalAnswerResponse entries.",
    )
    cache_semantic_similarity_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Cosine-similarity threshold for semantic near-duplicate cache hits.",
    )
    cache_semantic_max_entries: int = Field(
        default=100,
        ge=1,
        description="Max recent query embeddings kept per user_type for semantic cache lookup.",
    )
    rate_limit_per_minute: int = 30
    rate_limit_tier_limits: str = Field(
        default="",
        description=(
            'Comma-separated tier:requests_per_minute pairs (e.g. "standard:30,premium:100"). '
            "Tiers not listed fall back to rate_limit_per_minute."
        ),
    )

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
