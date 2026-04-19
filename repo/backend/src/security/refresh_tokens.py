"""
Refresh token primitives.

Tokens are opaque high-entropy strings. Only their SHA-256 hash is persisted so
a DB breach cannot replay live refresh tokens. Rotation and reuse-detection
(family invalidation) live in `services/auth_service.py`.
"""
from __future__ import annotations

import hashlib
import secrets

REFRESH_TOKEN_BYTES = 48  # 384 bits of entropy


def generate_opaque_token() -> str:
    """Return a URL-safe opaque refresh token."""
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    """Deterministic SHA-256 hash in hex; stored in refresh_tokens.token_hash."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
