"""
Condense-question step: rewrites multi-turn follow-ups into standalone queries.

See PLAN.md Section 5 and TASKS.md T29.
"""


async def condense_question(llm, question: str, history: list[dict]) -> str:
    """Rewrite `question` into a standalone query given prior session history.

    Returns the original question unchanged (no LLM call) if there is no
    prior history.

    TODO: implement the LLM-based rewrite for the non-empty-history case.
    """
    if not history:
        return question
    raise NotImplementedError
