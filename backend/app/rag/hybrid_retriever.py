"""
Hybrid retrieval: fuses FAISS (semantic) and BM25 (keyword) results via
Reciprocal Rank Fusion using LangChain's EnsembleRetriever.

See PLAN.md Section 4 and TASKS.md T18.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever

from app.core.config import settings
from app.core.logging import logger
from app.rag.bm25_index import Bm25QueryResult, query_bm25_index
from app.rag.vectorstore import FaissQueryResult, query_faiss_index

# Metadata key EnsembleRetriever uses to identify/dedupe documents across the
# two legs. Every indexed chunk carries a `source_citation` (see
# vectorstore.chunk_to_document), which is a more reliable identity than raw
# page_content (LangChain's default `id_key=None` behaviour).
HYBRID_ID_KEY = "source_citation"

# Matches EnsembleRetriever's default `c` constant so our score recomputation
# below stays numerically consistent with the fusion it performs internally.
DEFAULT_RRF_CONSTANT = 60

_QueryHit = FaissQueryResult | Bm25QueryResult


@dataclass(frozen=True)
class HybridQueryResult:
    """A single fused retrieval hit with citation metadata and a normalized score."""

    text: str
    score: float
    domain: str
    act_name: str
    act_year: int
    chapter: str | None
    section_number: str
    section_title: str | None
    source_citation: str


def build_hybrid_retriever(
    faiss_retriever: BaseRetriever,
    bm25_retriever: BaseRetriever,
    weights: tuple[float, float] = (0.5, 0.5),
) -> EnsembleRetriever:
    """Combine the two retrievers into a single `EnsembleRetriever`.

    `weights` is `(semantic_weight, keyword_weight)`; pass explicit values to
    override `settings.hybrid_semantic_weight`/`hybrid_keyword_weight`.
    """
    if len(weights) != 2:
        raise ValueError("weights must contain exactly two values (semantic, keyword)")

    return EnsembleRetriever(
        retrievers=[faiss_retriever, bm25_retriever],
        weights=list(weights),
        id_key=HYBRID_ID_KEY,
    )


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalize a list of raw fused scores to the [0, 1] range."""
    if not scores:
        return []

    lo, hi = min(scores), max(scores)
    if math.isclose(hi, lo):
        # All scores are (numerically) identical - equally confident, not zero.
        return [1.0 for _ in scores]

    return [(score - lo) / (hi - lo) for score in scores]


def _weighted_reciprocal_rank_scores(
    ranked_id_lists: list[list[str]],
    weights: tuple[float, float],
    c: int = DEFAULT_RRF_CONSTANT,
) -> dict[str, float]:
    """Recompute per-document weighted-RRF scores for the two ranked legs.

    `EnsembleRetriever.invoke()` only returns the final fused document order,
    not the underlying scores, so citations/confidence scoring (T21/T25) have
    nothing to attach as `retrieval_score`. This mirrors LangChain's published
    formula (`weight / (rank + c)`, see `EnsembleRetriever.weighted_reciprocal_rank`)
    rather than inventing a bespoke scheme.
    """
    scores: dict[str, float] = defaultdict(float)
    for ranked_ids, weight in zip(ranked_id_lists, weights, strict=True):
        for rank, doc_id in enumerate(ranked_ids, start=1):
            scores[doc_id] += weight / (rank + c)
    return scores


def query_hybrid_index(
    faiss_index,
    bm25_index,
    query: str,
    k: int = 20,
    domain: str | None = None,
    weights: tuple[float, float] | None = None,
) -> list[HybridQueryResult]:
    """Query both indices and return the weighted-RRF-fused top-K results.

    Domain filtering is delegated to each leg's own query function (both
    already support it), then results are fused and normalized to [0, 1].
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    logger.info("Vector search started")
    try:
        resolved_weights = weights or (settings.hybrid_semantic_weight, settings.hybrid_keyword_weight)
        fetch_k = max(k * 3, settings.retrieval_top_k)

        faiss_hits = query_faiss_index(faiss_index, query, k=fetch_k, domain=domain)
        bm25_hits = query_bm25_index(bm25_index, query, k=fetch_k, domain=domain)

        hits_by_citation: dict[str, _QueryHit] = {}
        all_hits: list[_QueryHit] = [*faiss_hits, *bm25_hits]
        for hit in all_hits:
            hits_by_citation.setdefault(hit.source_citation, hit)

        rrf_scores = _weighted_reciprocal_rank_scores(
            [
                [hit.source_citation for hit in faiss_hits],
                [hit.source_citation for hit in bm25_hits],
            ],
            resolved_weights,
        )

        fused_ids = sorted(hits_by_citation, key=lambda cid: rrf_scores[cid], reverse=True)
        normalized_scores = normalize_scores([rrf_scores[cid] for cid in fused_ids])

        results = [
            HybridQueryResult(
                text=hits_by_citation[citation_id].text,
                score=score,
                domain=hits_by_citation[citation_id].domain,
                act_name=hits_by_citation[citation_id].act_name,
                act_year=hits_by_citation[citation_id].act_year,
                chapter=hits_by_citation[citation_id].chapter,
                section_number=hits_by_citation[citation_id].section_number,
                section_title=hits_by_citation[citation_id].section_title,
                source_citation=citation_id,
            )
            for citation_id, score in zip(fused_ids, normalized_scores)
        ]
        logger.info("Vector search completed")
        return results[:k]
    except Exception as exc:
        logger.exception("Vector search failed: %s", type(exc).__name__)
        raise
