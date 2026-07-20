"""
Bearer-token authentication dependency.

Validates the Authorization header against the token->tier mapping derived
from Settings.backend_api_tokens. See PLAN.md Section 8 and TASKS.md T34.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logging import logger

bearer_scheme = HTTPBearer(auto_error=False)


def parse_token_tier_mapping(raw: str) -> dict[str, str]:
    """Parse a comma-separated ``token:tier`` config string into a mapping.

    Example: ``"dev-token:standard,premium-key:premium"``.
    """
    mapping: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        token, separator, tier = entry.partition(":")
        if not separator or not token.strip() or not tier.strip():
            raise ValueError(f"Invalid BACKEND_API_TOKENS entry: {entry!r} (expected token:tier)")
        mapping[token.strip()] = tier.strip()
    return mapping


@lru_cache(maxsize=1)
def get_token_tier_mapping() -> dict[str, str]:
    """Return the token->tier mapping loaded from settings (cached)."""
    return parse_token_tier_mapping(settings.backend_api_tokens)


def reset_token_tier_mapping_cache() -> None:
    """Clear the cached token mapping (for tests and config reloads)."""
    get_token_tier_mapping.cache_clear()


def get_token_tier(token: str) -> str | None:
    """Look up the rate-limit tier for a validated bearer token."""
    return get_token_tier_mapping().get(token)


async def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Validate the bearer token and return the resolved token identifier.

    Raises HTTP 401 when the header is missing, malformed, or the token is
    not present in the configured mapping.
    """
    if credentials is None:
        logger.error("Authentication failed: Missing bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    if credentials.scheme.lower() != "bearer":
        logger.error("Authentication failed: Invalid authorization scheme")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme; Bearer token required",
        )

    token = credentials.credentials
    if token not in get_token_tier_mapping():
        logger.error("Authentication failed: Invalid bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )

    return token
