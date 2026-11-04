"""Security utilities for salted password hashing and JWT token handling."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

# Default secret key (can be overridden via AUTH_SECRET_KEY env var)
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "devops-swarm-super-secret-production-key-2026")
ALGORITHM = "HS256"
DEFAULT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Hash a plaintext password using salted PBKDF2-HMAC-SHA256 (100,000 iterations)."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${pw_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hashed password using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hash = parts[3]
        pw_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(pw_hash.hex(), expected_hash)
    except Exception:
        return False


def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_url_decode(input_str: str) -> bytes:
    padding = "=" * ((4 - len(input_str) % 4) % 4)
    return base64.urlsafe_b64decode(input_str + padding)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token containing subject and claims."""
    header = {"alg": ALGORITHM, "typ": "JWT"}
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=DEFAULT_EXPIRE_MINUTES))
    payload = {
        **data,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    unsigned_token = f"{_b64_url_encode(header_bytes)}.{_b64_url_encode(payload_bytes)}"
    signature = hmac.new(SECRET_KEY.encode("utf-8"), unsigned_token.encode("utf-8"), hashlib.sha256).digest()
    return f"{unsigned_token}.{_b64_url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a signed JWT token. Raises ValueError on expiration or signature tampering."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, signature_b64 = parts
    unsigned_token = f"{header_b64}.{payload_b64}"

    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), unsigned_token.encode("utf-8"), hashlib.sha256).digest()
    actual_sig = _b64_url_decode(signature_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    payload_json = _b64_url_decode(payload_b64).decode("utf-8")
    payload = json.loads(payload_json)

    exp = payload.get("exp")
    if exp and datetime.now(UTC).timestamp() > exp:
        raise ValueError("Token has expired")

    return payload
