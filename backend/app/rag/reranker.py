"""
Optional cross-encoder re-ranking stage, gated by ENABLE_RERANKER.

See PLAN.md Section 4 and TASKS.md T19.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.cross_encoders import BaseCrossEncoder
from langchain_core.retrievers import BaseRetriever

from app.core.config import settings


@lru_cache(maxsize=4)
def get_cross_encoder_model(model_name: str | None = None) -> HuggingFaceCrossEncoder:
    """Return a configured HuggingFace cross-encoder model instance.

    Mirrors ``app.rag.embeddings.get_embedding_model``: the model name is read
    from ``settings.reranker_model`` unless an explicit ``model_name``
    override is supplied (useful in tests). Instances are cached per resolved
    model name so repeated calls (e.g. once per chain invocation) don't
    reload weights.
    """
    resolved_name = model_name or settings.reranker_model
    return HuggingFaceCrossEncoder(
        model_name=resolved_name,
        model_kwargs={"device": "cpu"},
    )


def reset_cross_encoder_model_cache() -> None:
    """Clear the cross-encoder model singleton cache (for tests and config reloads)."""
    get_cross_encoder_model.cache_clear()


def build_reranking_retriever(
    base_retriever: BaseRetriever,
    top_n: int | None = None,
    cross_encoder: BaseCrossEncoder | None = None,
) -> BaseRetriever:
    """Wrap `base_retriever` with a cross-encoder reranker when
    `settings.enable_reranker` is True; otherwise return it unchanged.

    Uses `ContextualCompressionRetriever` + `CrossEncoderReranker` over a
    HuggingFace cross-encoder (default `ms-marco-MiniLM-L-6-v2`), per
    PLAN.md Section 4. `cross_encoder` is an override hook for tests (avoids
    loading the real HuggingFace model); production callers should omit it.
    """
    if not settings.enable_reranker:
        return base_retriever

    reranker = CrossEncoderReranker(
        model=cross_encoder or get_cross_encoder_model(),
        top_n=top_n if top_n is not None else settings.rerank_top_n,
    )
    return ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=base_retriever,
    )
