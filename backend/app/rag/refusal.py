"""
Refusal/fallback decision logic (pre- and post-generation) and canned templates.

See PLAN.md Section 7 and TASKS.md T26.
"""

REFUSAL_TEMPLATE = (
    "I don't have sufficient reliable information to answer this confidently. "
    "Please consult a licensed lawyer for advice on this matter."
)


def should_refuse_before_generation(best_retrieval_score: float, threshold: float) -> bool:
    """Return True if retrieval quality is too low to attempt generation at all.

    TODO: implement using `app.core.config.settings.confidence_refusal_threshold`.
    """
    raise NotImplementedError


def should_refuse_after_generation(confidence_score: float, threshold: float) -> bool:
    """Return True if the computed confidence is too low to serve the LLM's answer.

    TODO: implement.
    """
    raise NotImplementedError
