"""
GET /api/v1/health - unauthenticated liveness check.

See TASKS.md T39.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Basic liveness probe; intentionally has no dependencies (no auth, no DB)."""
    return {"status": "ok"}
