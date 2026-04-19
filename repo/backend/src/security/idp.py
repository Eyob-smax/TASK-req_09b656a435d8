"""
Internal Identity Provider helpers.

The IdP is a first-party FastAPI module: trusted internal clients authenticate
with client_credentials and receive a signed JWT from the same RSA keypair
that signs application access tokens. No external IdP or federation.
"""
from __future__ import annotations

from ..domain.enums import UserRole  # noqa: F401 (re-exported for downstream)
from .jwt import create_access_token
from .passwords import verify_password


def verify_client_secret(client_secret_plain: str, client_secret_hash: str) -> bool:
    return verify_password(client_secret_plain, client_secret_hash)


def build_client_credentials_token(
    *,
    client_id: str,
    scopes: list[str],
    ttl_seconds: int = 15 * 60,
) -> str:
    extra = {"aud": "internal", "scope": " ".join(scopes), "client_id": client_id}
    return create_access_token(
        user_id=client_id,
        role=None,
        extra_claims=extra,
        ttl_seconds=ttl_seconds,
    )


def parse_scope(scope_string: str, allowed: str) -> list[str]:
    requested = [s.strip() for s in (scope_string or "").split() if s.strip()]
    allowed_set = {s.strip() for s in (allowed or "").split() if s.strip()}
    if not requested:
        return sorted(allowed_set)
    return [s for s in requested if s in allowed_set]
