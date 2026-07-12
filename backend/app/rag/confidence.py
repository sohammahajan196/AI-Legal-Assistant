"""
Server-side confidence scoring: combines retrieval similarity and answer
groundedness. Must never be derived solely from the LLM's self-reported
confidence (see general.mdc).

See PLAN.md Section 7 and TASKS.md T25.
"""

from __future__ import annotations

import math

from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.rag.embeddings import get_embedding_model
from app.schemas.legal_answer import SourceCitation


def compute_retrieval_component(used_citations: list[SourceCitation]) -> float:
    """Normalized fused retrieval score of the citations actually used.

    Each `SourceCitation.retrieval_score` is already the fused hybrid-retrieval
    score normalized to [0, 1] (see `app.rag.hybrid_retriever.normalize_scores`).
    Averaging across the citations the LLM actually relied on (not all
    candidates that were merely retrieved) rewards answers grounded in
    strongly-matched sources. An answer that used no citations has no
    retrieval quality to point to, so it scores 0.
    """
    if not used_citations:
        return 0.0

    scores = [citation.retrieval_score for citation in used_citations]
    return sum(scores) / len(scores)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def compute_groundedness_component(
    answer_text: str,
    citations: list[SourceCitation],
    embedding_model: Embeddings | None = None,
) -> float:
    """Embedding-similarity overlap between the answer and its cited excerpts.

    Cosine similarity is computed between the answer text and each cited
    excerpt, then averaged - a cheap automated "did the answer actually come
    from the source" check (PLAN.md Section 7). Negative similarities are
    floored at 0 so an inverse-correlated excerpt can't inflate the score of
    another. `embedding_model` is an override hook for tests (avoids loading
    the real HuggingFace model); production callers should omit it and rely
    on the cached model from `app.rag.embeddings`.
    """
    if not citations or not answer_text.strip():
        return 0.0

    model = embedding_model or get_embedding_model()
    answer_vector = model.embed_query(answer_text)
    excerpt_vectors = model.embed_documents([citation.excerpt for citation in citations])

    similarities = [
        max(0.0, _cosine_similarity(answer_vector, excerpt_vector)) for excerpt_vector in excerpt_vectors
    ]
    return sum(similarities) / len(similarities)


def compute_confidence_score(
    retrieval_component: float,
    groundedness_component: float,
    w1: float | None = None,
    w2: float | None = None,
) -> float:
    """Weighted combination of the two components into a final [0, 1] score.

    Weights default to `settings.confidence_retrieval_weight` /
    `settings.confidence_groundedness_weight` (configurable per T25's
    acceptance criteria) rather than being hardcoded at call sites; pass
    `w1`/`w2` explicitly to override. The result is clamped to [0, 1] so
    misconfigured weights (e.g. not summing to 1) can't push the score
    outside the range the API contract promises.
    """
    resolved_w1 = settings.confidence_retrieval_weight if w1 is None else w1
    resolved_w2 = settings.confidence_groundedness_weight if w2 is None else w2

    score = resolved_w1 * retrieval_component + resolved_w2 * groundedness_component
    return max(0.0, min(1.0, score))
