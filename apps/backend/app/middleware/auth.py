"""Bearer token authentication middleware."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Header

from app.config import settings


async def verify_api_key(authorization: str = Header(...)) -> str:
    """Validate Bearer token and return the token on success.
    
    Raises:
        HTTPException 401: If Authorization header is missing, malformed,
                          or does not match the configured API secret key.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header — expected: Bearer <token>",
        )
    token = authorization[len("Bearer ") :]
    if not settings.api_secret_key:
        raise HTTPException(status_code=500, detail="API_SECRET_KEY not configured on server")
    if token != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
