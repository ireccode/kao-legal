"""Cognito JWT verification middleware."""

from functools import lru_cache

import httpx
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from kao_legal.config.settings import get_settings

security = HTTPBearer()


@lru_cache(maxsize=1)
def _get_jwks(jwks_url: str) -> dict:
    """Fetch and cache JWKS from Cognito. Cache invalidates on restart."""
    response = httpx.get(jwks_url, timeout=10.0)
    response.raise_for_status()
    return response.json()


def _get_jwks_url(settings) -> str:
    return (
        f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )


async def verify_cognito_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """
    Verify Cognito JWT and return claims.

    Args:
        credentials: Bearer token from Authorization header.

    Returns:
        Decoded JWT claims dict containing user info (sub, email, etc.).

    Raises:
        HTTPException 401: If token is missing, expired, or invalid.
    """
    settings = get_settings()
    token = credentials.credentials
    jwks_url = _get_jwks_url(settings)

    try:
        jwks = _get_jwks(jwks_url)
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
        )
        return claims
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
