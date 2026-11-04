"""FastAPI dependencies for extracting and verifying authenticated users."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


def _extract_token(request: Request, credentials: Any) -> str | None:
    if isinstance(credentials, HTTPAuthorizationCredentials) and credentials.credentials:
        return credentials.credentials
    auth_header = request.headers.get("authorization") if hasattr(request, "headers") else None
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict[str, Any]:
    """Retrieve the currently authenticated user or raise HTTP 401."""
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired access token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
        )

    user_repo = getattr(request.app.state, "user_repository", None)
    if user_repo is not None:
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token no longer exists.",
            )
        return user

    # Fallback to payload data if repo is not available
    return {
        "id": user_id,
        "email": payload.get("email", ""),
        "name": payload.get("name", "User"),
        "created_at": payload.get("created_at", ""),
    }


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict[str, Any] | None:
    """Retrieve user if token is provided and valid; otherwise return None."""
    token = _extract_token(request, credentials)
    if not token:
        return None
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None
