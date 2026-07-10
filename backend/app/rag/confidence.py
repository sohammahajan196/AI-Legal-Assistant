"""
Server-side confidence scoring: combines retrieval similarity and answer
groundedness. Must never be derived solely from the LLM's self-reported
confidence (see general.mdc).

See PLAN.md Section 7 and TASKS.md T25.
"""

from app.schemas.legal_answer import SourceCitation


def compute_retrieval_component(used_citations: list[SourceCitation]) -> float:
    """Normalized fused retrieval score of the citations actually used.

    TODO: implement.
    """
    raise NotImplementedError


def compute_groundedness_component(answer_text: str, citations: list[SourceCitation]) -> float:
    """Embedding-similarity overlap between the answer and its cited excerpts.

    TODO: implement.
    """
    raise NotImplementedError


def compute_confidence_score(
    retrieval_component: float,
    groundedness_component: float,
    w1: float = 0.5,
    w2: float = 0.5,
) -> float:
    """Weighted combination of the two components into a final [0, 1] score.

    TODO: implement; weights should come from Settings, not be hardcoded
    at call sites.
    """
    raise NotImplementedError
