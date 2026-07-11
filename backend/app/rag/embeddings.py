"""
HuggingFace embedding model wrapper.

See PLAN.md Section 3 and TASKS.md T14.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

# Vector dimension for the default retrieval model (BAAI/bge-base-en-v1.5).
BGE_BASE_EN_V1_5_DIMENSION = 768

KNOWN_EMBEDDING_DIMENSIONS: dict[str, int] = {
    "BAAI/bge-base-en-v1.5": BGE_BASE_EN_V1_5_DIMENSION,
}


def expected_embedding_dimension(model_name: str | None = None) -> int | None:
    """Return the known output dimension for a configured model, if documented."""
    name = model_name or settings.embedding_model
    return KNOWN_EMBEDDING_DIMENSIONS.get(name)


@lru_cache(maxsize=4)
def get_embedding_model(model_name: str | None = None) -> HuggingFaceEmbeddings:
    """Return a configured HuggingFace embedding model instance.

    The model name is read from ``settings.embedding_model`` unless an explicit
    ``model_name`` override is supplied (useful in tests). Instances are cached
    per resolved model name so repeated calls do not reload weights.
    """
    resolved_name = model_name or settings.embedding_model
    return HuggingFaceEmbeddings(
        model_name=resolved_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def reset_embedding_model_cache() -> None:
    """Clear the embedding model singleton cache (for tests and config reloads)."""
    get_embedding_model.cache_clear()
