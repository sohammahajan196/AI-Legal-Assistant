"""
Request/response models for the FastAPI chat endpoints.

See PLAN.md Section 8 and TASKS.md T21.
"""

from pydantic import BaseModel

from app.schemas.legal_answer import LegalAnswerResponse


class ChatRequest(BaseModel):
    """Incoming payload for POST /api/v1/chat."""

    query: str
    session_id: str | None = None
    user_type: str = "layperson"
    consent_to_log: bool = True


class ChatResponse(LegalAnswerResponse):
    """Response payload for POST /api/v1/chat.

    Currently identical to `LegalAnswerResponse`; kept as a distinct type in
    case API-only fields (e.g. `from_cache`) are needed later without
    changing the core RAG contract.
    """

    pass
