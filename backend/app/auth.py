"""Authentication, password security, and JWT token management."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, Request, status

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "devops-swarm-secure-auth-secret-key-prod-change-in-env")
DEFAULT_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
REMEMBER_ME_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days


class TokenError(Exception):
    """Base class for token-related errors."""


class TokenExpiredError(TokenError):
    """Raised when a token has passed its expiration time."""


class TokenInvalidError(TokenError):
    """Raised when a token format or signature is invalid."""


def hash_password(password: str) -> str:
    """Securely hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash using constant-time comparison."""
    if not hashed_password or not plain_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hash = parts[3]
        derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(derived.hex(), expected_hash)
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("ascii"))


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    secret_key: str = AUTH_SECRET_KEY,
) -> tuple[str, int]:
    """Generate a signed expiring JWT token. Returns (token_string, expires_in_seconds)."""
    now = int(time.time())
    expires_in = int(expires_delta.total_seconds()) if expires_delta else (DEFAULT_EXPIRE_MINUTES * 60)
    expire_timestamp = now + expires_in

    payload = {
        **data,
        "iat": now,
        "exp": expire_timestamp,
    }

    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    header_b64 = _b64url_encode(header_bytes)
    payload_b64 = _b64url_encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    token = f"{header_b64}.{payload_b64}.{sig_b64}"
    return token, expires_in


def decode_access_token(token: str, secret_key: str = AUTH_SECRET_KEY) -> dict[str, Any]:
    """Decode and verify a signed JWT token."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise TokenInvalidError("Malformed token structure")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception as exc:
        raise TokenInvalidError("Invalid token signature encoding") from exc

    if not hmac.compare_digest(actual_sig, expected_sig):
        raise TokenInvalidError("Token signature verification failed")

    try:
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception as exc:
        raise TokenInvalidError("Invalid token payload") from exc

    exp = payload.get("exp")
    if exp is None or int(time.time()) > exp:
        raise TokenExpiredError("Token has expired")

    return payload


async def get_current_user(request: Request) -> dict[str, Any]:
    """FastAPI dependency to extract and authenticate the current user from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    try:
        payload = decode_access_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token payload is missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = getattr(request.app.state, "user_repository", None)
    if not user_repo:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User repository service is unavailable.",
        )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists or has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return safe user dictionary without password_hash
    return {k: v for k, v in user.items() if k != "password_hash"}

