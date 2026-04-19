"""
JWT RS256 issuance/verification.

Uses `install_keys()` to inject a dev keypair into the jwt module so the
test does not touch the filesystem or settings.
"""
import base64
import json

import pytest

from src.security import jwt as jwt_mod
from src.security.errors import TokenExpiredError, TokenInvalidError


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://test:test@localhost/test")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)


@pytest.fixture(autouse=True)
def _install_keys():
    priv, pub = jwt_mod.generate_dev_keypair()
    jwt_mod.install_keys(priv, pub)
    yield
    jwt_mod.install_keys(None, None)  # type: ignore[arg-type]


def test_encode_decode_roundtrip():
    token = jwt_mod.create_access_token(user_id="11111111-1111-1111-1111-111111111111", role="candidate")
    claims = jwt_mod.decode_access_token(token)
    assert claims["sub"] == "11111111-1111-1111-1111-111111111111"
    assert claims["role"] == "candidate"


def test_expired_token_raises():
    token = jwt_mod.create_access_token(
        user_id="11111111-1111-1111-1111-111111111111", role="candidate", ttl_seconds=-10
    )
    with pytest.raises(TokenExpiredError):
        jwt_mod.decode_access_token(token)


def test_tampered_token_raises():
    token = jwt_mod.create_access_token(user_id="id", role="admin")
    # Flip one character in the signature segment
    parts = token.split(".")
    sig = bytearray(base64.urlsafe_b64decode(parts[2] + "=="))
    sig[0] ^= 0xFF
    parts[2] = base64.urlsafe_b64encode(bytes(sig)).rstrip(b"=").decode("ascii")
    tampered = ".".join(parts)
    with pytest.raises(TokenInvalidError):
        jwt_mod.decode_access_token(tampered)


def test_algorithm_confusion_rejected():
    # Build an HS256 token with the public key as the HMAC secret — must be rejected.
    import jose.jwt as jose_jwt

    _, pub = jwt_mod._ensure_keys()  # type: ignore[attr-defined]
    attacker_token = jose_jwt.encode(
        {"sub": "attacker", "iss": "merittrack", "aud": "merittrack-app", "exp": 9999999999},
        pub.decode(),
        algorithm="HS256",
    )
    with pytest.raises(TokenInvalidError):
        jwt_mod.decode_access_token(attacker_token)


def test_jwks_exposes_public_key():
    jwks = jwt_mod.get_jwks()
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
    key = jwks["keys"][0]
    assert key["kty"] == "RSA"
    assert key["alg"] == "RS256"
    assert key["use"] == "sig"
    assert "n" in key and "e" in key
    assert key["kid"]


def test_extra_claims_carried():
    token = jwt_mod.create_access_token(
        user_id="u1", role="admin", extra_claims={"family_id": "fam-1"}
    )
    claims = jwt_mod.decode_access_token(token)
    assert claims["family_id"] == "fam-1"
