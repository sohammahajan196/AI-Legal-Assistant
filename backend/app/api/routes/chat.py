"""
POST /api/v1/chat - the main Q&A endpoint.

Wires bearer-token auth -> rate limiting -> app.services.chat_service ->
consent-aware query logging. See PLAN.md Section 8 and TASKS.md T37.
"""

from fastapi import APIRouter

router = APIRouter(tags=["chat"])

# TODO: define POST /chat accepting app.schemas.chat.ChatRequest and
# returning app.schemas.chat.ChatResponse, calling
# app.services.chat_service.handle_chat_request. Must require
# app.core.security.verify_bearer_token and app.core.rate_limit.
