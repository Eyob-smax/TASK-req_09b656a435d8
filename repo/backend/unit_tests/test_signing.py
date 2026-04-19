"""
Canonical-string bytes + ECDSA P-256 verification.
"""
import base64

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from src.security.signing import build_canonical_string, verify_signature


def _sign(message: bytes) -> tuple[str, str]:
    """Generate a fresh P-256 keypair, sign the message, return (pem, b64_sig)."""
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    sig = priv.sign(message, ec.ECDSA(hashes.SHA256()))
    return pub_pem, base64.b64encode(sig).decode()


def test_canonical_string_bytes_are_exact():
    result = build_canonical_string(
        method="POST",
        path="/api/v1/orders",
        timestamp="2026-04-18T12:00:00Z",
        nonce="abc",
        device_id="dev-1",
        body_bytes=b'{"x":1}',
    )
    expected = (
        b"POST\n"
        b"/api/v1/orders\n"
        b"2026-04-18T12:00:00Z\n"
        b"abc\n"
        b"dev-1\n"
        + b"e3b5e88d3c7c3c1b2fdfd3f43bb10196a5c36da1ea12ca32bd3f60c6ff65d5f9\n"  # placeholder
    )
    assert result.startswith(b"POST\n/api/v1/orders\n2026-04-18T12:00:00Z\nabc\ndev-1\n")
    # body hash must be 64 hex chars + trailing newline
    tail = result.split(b"\n")[-2]
    assert len(tail) == 64


def test_verify_signature_pass_roundtrip():
    msg = build_canonical_string("POST", "/api/v1/orders", "2026-04-18T12:00:00Z", "n", "d", b"")
    pem, sig = _sign(msg)
    assert verify_signature(pem, msg, sig) is True


def test_verify_signature_tampered_body_fails():
    msg_original = build_canonical_string("POST", "/api/v1/orders", "t", "n", "d", b"")
    pem, sig = _sign(msg_original)
    msg_tampered = build_canonical_string("POST", "/api/v1/orders", "t", "n", "d", b"hacked")
    assert verify_signature(pem, msg_tampered, sig) is False


def test_verify_signature_tampered_path_fails():
    pem, sig = _sign(build_canonical_string("POST", "/api/v1/orders", "t", "n", "d", b""))
    other = build_canonical_string("POST", "/api/v1/admin/users", "t", "n", "d", b"")
    assert verify_signature(pem, other, sig) is False


def test_verify_signature_bad_b64_raises():
    from src.security.errors import SignatureInvalidError

    pem, _ = _sign(build_canonical_string("POST", "/x", "t", "n", "d", b""))
    with pytest.raises(SignatureInvalidError):
        verify_signature(pem, b"anything", "%%%not-b64%%%")


def test_verify_signature_raw_r_s_accepted():
    """WebCrypto emits raw r||s — verify() must accept either DER or raw."""
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    message = build_canonical_string("GET", "/api/v1/auth/me", "t", "n", "d", b"")
    der_sig = priv.sign(message, ec.ECDSA(hashes.SHA256()))
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

    r, s = decode_dss_signature(der_sig)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    assert verify_signature(pub_pem, message, base64.b64encode(raw).decode()) is True
