"""
Response caching: Redis exact-match cache + semantic near-duplicate query cache.

See PLAN.md Section 9 and TASKS.md T32.
"""

from app.schemas.legal_answer import LegalAnswerResponse


async def get_cached_response(query: str, user_type: str) -> LegalAnswerResponse | None:
    """Return a cached response if one exists for this (or a near-duplicate)
    query, else None.

    TODO: implement exact-match + semantic near-duplicate (cosine > 0.95)
    lookup. Must degrade gracefully (return None) if Redis is unreachable,
    per database.mdc.
    """
    raise NotImplementedError


async def set_cached_response(query: str, user_type: str, response: LegalAnswerResponse) -> None:
    """Store a response in the cache with a configured TTL.

    TODO: implement.
    """
    raise NotImplementedError
