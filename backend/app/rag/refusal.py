"""
Refusal/fallback decision logic (pre- and post-generation) and canned templates.

See PLAN.md Section 7 and TASKS.md T26.
"""

from __future__ import annotations

from app.core.config import settings
from app.schemas.legal_answer import LegalAnswerResponse, LegalDomain, SourceCitation

REFUSAL_TEMPLATE = (
    "I don't have sufficient reliable information to answer this confidently. "
    "Please consult a licensed lawyer for advice on this matter."
)


def should_refuse_before_generation(best_retrieval_score: float, threshold: float | None = None) -> bool:
    """Return True if retrieval quality is too low to attempt generation at all.

    Pre-generation short-circuit (PLAN.md Section 7): when the best fused
    hybrid-retrieval score doesn't clear the threshold, there is nothing
    trustworthy to ground an answer in, so callers must skip the LLM call
    entirely rather than let it hallucinate from weak context. `threshold`
    defaults to `settings.confidence_refusal_threshold` when omitted.
    """
    resolved_threshold = settings.confidence_refusal_threshold if threshold is None else threshold
    return best_retrieval_score < resolved_threshold


def should_refuse_after_generation(confidence_score: float, threshold: float | None = None) -> bool:
    """Return True if the computed confidence is too low to serve the LLM's answer.

    Post-generation override (PLAN.md Section 7): applied even after a
    structurally valid answer was generated, using the server-computed
    `confidence_score` (never the LLM's own self-reported confidence - see
    app.rag.confidence and general.mdc). `threshold` defaults to
    `settings.confidence_refusal_threshold` when omitted.
    """
    resolved_threshold = settings.confidence_refusal_threshold if threshold is None else threshold
    return confidence_score < resolved_threshold


def build_refusal_response(
    legal_domain: LegalDomain,
    disclaimer: str,
    citations: list[SourceCitation] | None = None,
    confidence_score: float = 0.0,
) -> LegalAnswerResponse:
    """Assemble the final response for a refusal outcome.

    Overrides the answer with the canned `REFUSAL_TEMPLATE` and sets
    `is_refusal=True`, but deliberately *retains* whatever citations were
    found (even low-confidence ones) instead of discarding them - PLAN.md
    Section 7 requires still showing sources, marked low-confidence, for
    transparency even when the answer itself is refused.
    """
    return LegalAnswerResponse(
        answer=REFUSAL_TEMPLATE,
        confidence_score=confidence_score,
        legal_domain=legal_domain,
        citations=citations or [],
        is_refusal=True,
        disclaimer=disclaimer,
    )
