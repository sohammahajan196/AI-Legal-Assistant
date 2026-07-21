"""
GET /api/v1/health - unauthenticated liveness check (includes Redis PING).

See TASKS.md T39.
"""

from fastapi import APIRouter

from app.rag.cache import ping_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe plus Redis dependency status.

    Always returns HTTP 200 while the process is up (liveness). When Redis is
    unreachable the top-level ``status`` is ``degraded`` and ``redis`` is
    ``unavailable`` — the app still serves traffic via in-memory rate limits
    and cache skip, but operators can see the failure instead of guessing.
    """
    redis_ok = await ping_redis()
    redis_status = "ok" if redis_ok else "unavailable"
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": redis_status,
    }
