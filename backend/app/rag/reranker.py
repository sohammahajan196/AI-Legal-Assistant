"""
Optional cross-encoder re-ranking stage, gated by ENABLE_RERANKER.

See PLAN.md Section 4 and TASKS.md T19.
"""

from app.core.config import settings


def build_reranking_retriever(base_retriever):
    """Wrap `base_retriever` with a cross-encoder reranker when
    `settings.enable_reranker` is True; otherwise return it unchanged.

    TODO: implement using `ContextualCompressionRetriever` + a HuggingFace
    cross-encoder (e.g. ms-marco-MiniLM-L-6-v2).
    """
    if not settings.enable_reranker:
        return base_retriever
    raise NotImplementedError
