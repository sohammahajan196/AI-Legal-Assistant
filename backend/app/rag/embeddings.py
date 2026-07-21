"""
HuggingFace embedding model wrapper.

See PLAN.md Section 3 and TASKS.md T14.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

# Vector dimension for the default retrieval model (BAAI/bge-small-en-v1.5).
BGE_SMALL_EN_V1_5_DIMENSION = 384

KNOWN_EMBEDDING_DIMENSIONS: dict[str, int] = {
    "BAAI/bge-small-en-v1.5": BGE_SMALL_EN_V1_5_DIMENSION,
}


def expected_embedding_dimension(model_name: str | None = None) -> int | None:
    """Return the known output dimension for a configured model, if documented."""
    name = model_name or settings.embedding_model
    return KNOWN_EMBEDDING_DIMENSIONS.get(name)


@lru_cache(maxsize=4)
def _get_embedding_model_cached(resolved_name: str) -> HuggingFaceEmbeddings:
    """Process-wide singleton constructor keyed by resolved HuggingFace model id."""
    return HuggingFaceEmbeddings(
        model_name=resolved_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_embedding_model(model_name: str | None = None) -> HuggingFaceEmbeddings:
    """Return the shared HuggingFace embedding model for *model_name*.

    The model name is read from ``settings.embedding_model`` unless an explicit
    ``model_name`` override is supplied (useful in tests). Caching is keyed on
    the *resolved* name so ``get_embedding_model()`` and
    ``get_embedding_model(settings.embedding_model)`` reuse one instance —
    weights are loaded at most once per distinct model id per process.
    """
    resolved_name = model_name or settings.embedding_model
    return _get_embedding_model_cached(resolved_name)


def reset_embedding_model_cache() -> None:
    """Clear the embedding model singleton cache (for tests and config reloads)."""
    _get_embedding_model_cached.cache_clear()
