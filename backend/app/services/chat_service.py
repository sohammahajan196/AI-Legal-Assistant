"""
Chat service: the single entrypoint the API layer calls into.

Checks the cache, invokes the RAG chain, stores the result, and returns the
final response. See PLAN.md Section 9 and TASKS.md T33.
"""

from app.schemas.legal_answer import LegalAnswerResponse


async def handle_chat_request(
    query: str, session_id: str | None, user_type: str
) -> LegalAnswerResponse:
    """Orchestrate a single chat request end-to-end.

    TODO: wire app.rag.cache (check/store) and app.rag.chain.run_rag_chain,
    plus app.services.session_store for history. This must remain the ONLY
    entrypoint the API layer uses -- routes must not call app.rag.chain
    directly (see backend.mdc).
    """
    raise NotImplementedError
