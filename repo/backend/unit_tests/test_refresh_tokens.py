"""
Refresh token generation and hashing contract.
"""
from src.security.refresh_tokens import generate_opaque_token, hash_refresh_token


def test_hash_is_deterministic():
    t = "some-opaque-token"
    assert hash_refresh_token(t) == hash_refresh_token(t)


def test_hash_is_sha256_length_hex():
    h = hash_refresh_token("x")
    assert len(h) == 64
    int(h, 16)  # hex-decodes


def test_tokens_are_unique():
    seen = {generate_opaque_token() for _ in range(200)}
    assert len(seen) == 200


def test_token_is_sufficiently_long():
    t = generate_opaque_token()
    assert len(t) >= 48
