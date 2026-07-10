"""
Bearer-token authentication dependency.

Validates the Authorization header against the token->tier mapping derived
from Settings.backend_api_tokens. See PLAN.md Section 8 and TASKS.md T34.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


async def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Validate the bearer token and return the resolved token identifier.

    TODO: parse Settings.backend_api_tokens into a token->tier mapping and
    look up `credentials.credentials` against it, raising 401 on a miss.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    raise NotImplementedError
