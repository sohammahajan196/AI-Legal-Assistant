"""
Per-token rate limiting backed by Redis.

See PLAN.md Section 8 and TASKS.md T35.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.security import get_token_tier

logger = logging.getLogger(__name__)

_limiter: Limiter | None = None


def parse_rate_limit_tier_limits(raw: str) -> dict[str, int]:
    """Parse comma-separated ``tier:requests_per_minute`` pairs."""
    mapping: dict[str, int] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        tier, separator, rpm = entry.partition(":")
        if not separator or not tier.strip() or not rpm.strip():
            raise ValueError(
                f"Invalid RATE_LIMIT_TIER_LIMITS entry: {entry!r} (expected tier:requests_per_minute)"
            )
        mapping[tier.strip()] = int(rpm.strip())
    return mapping


@lru_cache(maxsize=1)
def get_rate_limit_tier_mapping() -> dict[str, int]:
    """Return tier->requests_per_minute limits loaded from settings."""
    if not settings.rate_limit_tier_limits.strip():
        return {}
    return parse_rate_limit_tier_limits(settings.rate_limit_tier_limits)


def reset_rate_limit_tier_mapping_cache() -> None:
    """Clear the cached tier-limit mapping (for tests and config reloads)."""
    get_rate_limit_tier_mapping.cache_clear()


def get_requests_per_minute_for_tier(tier: str) -> int:
    """Resolve the per-minute request budget for a bearer-token tier."""
    return get_rate_limit_tier_mapping().get(tier, settings.rate_limit_per_minute)


def _extract_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        return None
    return credentials


def get_rate_limit_key(request: Request) -> str:
    """Rate-limit counter key: the authenticated bearer token (per T35)."""
    token = _extract_bearer_token(request)
    return token if token is not None else "anonymous"


def get_rate_limit_string(key: str) -> str:
    """Dynamic slowapi limit string derived from the token's configured tier.

    slowapi passes the resolved ``key_func`` value (the bearer token) when
    the limit provider declares a ``key`` parameter.
    """
    if key == "anonymous":
        rpm = settings.rate_limit_per_minute
    else:
        tier = get_token_tier(key) or "unknown"
        rpm = get_requests_per_minute_for_tier(tier)
    return f"{rpm}/minute"


def create_limiter(storage_uri: str | None = None) -> Limiter:
    """Build a slowapi ``Limiter`` backed by Redis (or an override URI in tests)."""
    return Limiter(
        key_func=get_rate_limit_key,
        storage_uri=storage_uri or settings.redis_url,
        in_memory_fallback_enabled=True,
        headers_enabled=True,
        swallow_errors=False,
    )


def get_limiter() -> Limiter:
    """Return the process-wide limiter singleton."""
    global _limiter
    if _limiter is None:
        _limiter = create_limiter()
    return _limiter


def reset_limiter() -> None:
    """Reset the limiter singleton (for tests)."""
    global _limiter
    _limiter = None
    reset_rate_limit_tier_mapping_cache()


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a clear 429 payload when a token exceeds its configured rate."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Rate limit exceeded for this API token. "
                "Please wait until the current window resets and try again."
            ),
            "limit": str(exc.detail),
        },
    )


def register_rate_limiting(app: FastAPI, limiter: Limiter | None = None) -> Limiter:
    """Attach slowapi middleware and the 429 handler to a FastAPI app."""
    resolved_limiter = limiter or get_limiter()
    app.state.limiter = resolved_limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    return resolved_limiter
