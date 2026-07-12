"""
GET /api/v1/sessions/{id}/history - conversation history retrieval.

See PLAN.md Section 8 and TASKS.md T38.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import verify_bearer_token
from app.schemas.chat import HistoryMessage, SessionHistoryResponse
from app.services.session_store import get_history

router = APIRouter(tags=["sessions"])


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    _token: str = Depends(verify_bearer_token),
) -> SessionHistoryResponse:
    """Return the ordered message history for a session.

    An unknown `session_id` yields an empty message list (HTTP 200), not an
    error, mirroring `app.services.session_store.get_history`.
    """
    messages = get_history(session_id)
    return SessionHistoryResponse(
        session_id=session_id,
        messages=[HistoryMessage(**message) for message in messages],
    )
