"""
GET /api/v1/sessions/{id}/history - conversation history retrieval.

See PLAN.md Section 8 and TASKS.md T38.
"""

from fastapi import APIRouter

router = APIRouter(tags=["sessions"])

# TODO: define GET /sessions/{session_id}/history backed by
# app.services.session_store.get_history. Must require
# app.core.security.verify_bearer_token. Unknown session_id should return
# an empty list, not an error.
