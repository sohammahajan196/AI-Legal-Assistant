"""
POST /api/v1/chat - the main Q&A endpoint.

Wires bearer-token auth -> rate limiting -> app.services.chat_service ->
consent-aware query logging. See PLAN.md Section 8 and TASKS.md T37.
"""

from __future__ import annotations

import hashlib
import time

from fastapi import APIRouter, Depends, Request, Response

from app.core.config import settings
from app.core.rate_limit import get_limiter, get_rate_limit_string
from app.core.security import verify_bearer_token
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat_request
from app.services.query_log import log_query

router = APIRouter(tags=["chat"])
limiter = get_limiter()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _retrieved_chunk_ids(response: ChatResponse) -> list[str]:
    return [f"{citation.document}, S.{citation.section}" for citation in response.citations]


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(get_rate_limit_string)
async def chat(
    request: Request,
    response: Response,
    payload: ChatRequest,
    token: str = Depends(verify_bearer_token),
) -> ChatResponse:
    """Handle one authenticated chat request end-to-end.

    Fully async: awaits the chat service directly, then writes the audit log
    after the response is available. `log_query` catches its own failures
    (T36), so logging cannot fail the parent request.
    """
    start = time.perf_counter()
    response = await handle_chat_request(payload.query, payload.session_id, payload.user_type)
    latency_ms = (time.perf_counter() - start) * 1000
    chat_response = ChatResponse.model_validate(response.model_dump())

    log_query(
        token_hash=_hash_token(token),
        query=payload.query,
        consent_to_log=payload.consent_to_log,
        retrieved_chunk_ids=_retrieved_chunk_ids(chat_response),
        confidence_score=chat_response.confidence_score,
        latency_ms=latency_ms,
        model_used=settings.gemini_model,
    )

    return chat_response
