"""
RS256 JWT issuance and verification.

One RSA-2048 keypair signs both application access tokens and tokens issued
by the internal IdP. Public key is exposed via /api/v1/idp/jwks. Keys are
loaded lazily from paths declared in settings so tests can substitute keys
without touching the filesystem by calling `install_keys()`.
"""
from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt as jose_jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from ..config import get_settings
from .errors import TokenExpiredError, TokenInvalidError

_PRIVATE_KEY_PEM: bytes | None = None
_PUBLIC_KEY_PEM: bytes | None = None


def install_keys(private_pem: bytes, public_pem: bytes) -> None:
    """Test/bootstrap hook: inject key material without reading disk."""
    global _PRIVATE_KEY_PEM, _PUBLIC_KEY_PEM
    _PRIVATE_KEY_PEM = private_pem
    _PUBLIC_KEY_PEM = public_pem


def _load_keys_from_disk() -> tuple[bytes, bytes]:
    settings = get_settings()
    with open(settings.jwt_private_key_path, "rb") as f:
        priv = f.read()
    with open(settings.jwt_public_key_path, "rb") as f:
        pub = f.read()
    return priv, pub


def _ensure_keys() -> tuple[bytes, bytes]:
    global _PRIVATE_KEY_PEM, _PUBLIC_KEY_PEM
    if _PRIVATE_KEY_PEM is None or _PUBLIC_KEY_PEM is None:
        _PRIVATE_KEY_PEM, _PUBLIC_KEY_PEM = _load_keys_from_disk()
    return _PRIVATE_KEY_PEM, _PUBLIC_KEY_PEM


def generate_dev_keypair() -> tuple[bytes, bytes]:
    """Generate a fresh RSA-2048 keypair for tests / local bootstrap."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def create_access_token(
    *,
    user_id: str,
    role: str | None,
    extra_claims: dict | None = None,
    ttl_seconds: int = 15 * 60,
) -> str:
    settings = get_settings()
    priv, _ = _ensure_keys()
    now = datetime.now(tz=timezone.utc)
    payload: dict = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if role is not None:
        payload["role"] = role
    if extra_claims:
        payload.update(extra_claims)
    return jose_jwt.encode(
        payload,
        priv.decode("utf-8") if isinstance(priv, bytes) else priv,
        algorithm=settings.jwt_algorithm,
        headers={"kid": settings.jwt_key_id},
    )


def decode_access_token(token: str, *, audience: str | None = None) -> dict:
    settings = get_settings()
    _, pub = _ensure_keys()
    try:
        return jose_jwt.decode(
            token,
            pub.decode("utf-8") if isinstance(pub, bytes) else pub,
            algorithms=[settings.jwt_algorithm],
            audience=audience or settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Access token is expired.") from exc
    except JWTError as exc:
        raise TokenInvalidError("Access token is invalid.") from exc


def _int_to_b64url(n: int) -> str:
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode("ascii")


def get_jwks() -> dict:
    """Return public key in JWKS (RFC 7517) format."""
    settings = get_settings()
    _, pub_pem = _ensure_keys()
    pub_key = serialization.load_pem_public_key(pub_pem)
    numbers = pub_key.public_numbers()  # type: ignore[attr-defined]
    return {
        "keys": [
            {
                "kty": "RSA",
                "alg": settings.jwt_algorithm,
                "use": "sig",
                "kid": settings.jwt_key_id,
                "n": _int_to_b64url(numbers.n),
                "e": _int_to_b64url(numbers.e),
            }
        ]
    }
