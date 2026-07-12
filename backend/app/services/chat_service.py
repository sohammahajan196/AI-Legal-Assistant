"""
Chat service: the single entrypoint the API layer calls into.

Checks the cache, invokes the RAG chain, stores the result, and returns the
final response. See PLAN.md Section 9 and TASKS.md T33.

Response caching is always-on (keyed by normalized query + user_type, see
app.rag.cache). There is no per-request cache-bypass flag; ``consent_to_log``
on ``ChatRequest`` governs audit logging only (T36), not caching.
"""

from __future__ import annotations

import logging

from app.rag.cache import get_cached_response, set_cached_response
from app.rag.chain import run_rag_chain
from app.schemas.legal_answer import LegalAnswerResponse
from app.services.session_store import append_message, get_history

logger = logging.getLogger(__name__)


def _persist_messages(session_id: str | None, query: str, answer: str) -> None:
    """Append the user/assistant turn to session history when a session exists."""
    if not session_id:
        return
    try:
        append_message(session_id, "user", query)
        append_message(session_id, "assistant", answer)
    except ValueError:
        logger.warning("Skipping message persistence for unknown session_id=%s", session_id)


async def handle_chat_request(
    query: str, session_id: str | None, user_type: str
) -> LegalAnswerResponse:
    """Orchestrate a single chat request end-to-end.

    Checks the response cache first; on miss, fetches session history (if any),
    runs the RAG chain, stores the fresh result in cache, and persists the
    turn to the session store. This must remain the ONLY entrypoint the API
    layer uses -- routes must not call ``app.rag.chain`` directly (see
    backend.mdc).
    """
    history = get_history(session_id) if session_id else []

    cached = await get_cached_response(query, user_type)
    if cached is not None:
        _persist_messages(session_id, query, cached.answer)
        return cached

    response = await run_rag_chain(
        query,
        session_id,
        user_type,
        history=history,
    )

    await set_cached_response(query, user_type, response)
    _persist_messages(session_id, query, response.answer)
    return response
