"""
Canonical request signing + ECDSA P-256 verification.

Canonical form (newline-separated, trailing newline):
    METHOD\n
    PATH\n
    X-Timestamp\n
    X-Nonce\n
    X-Device-ID\n
    sha256(body)\n
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

from .errors import SignatureInvalidError


def build_canonical_string(
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    device_id: str,
    body_bytes: bytes,
) -> bytes:
    body_hash = hashlib.sha256(body_bytes or b"").hexdigest()
    parts = [
        method.upper(),
        path,
        timestamp,
        nonce,
        device_id,
        body_hash,
    ]
    return ("\n".join(parts) + "\n").encode("utf-8")


def load_public_key(public_key_pem: str):
    pem_bytes = public_key_pem.encode("utf-8") if isinstance(public_key_pem, str) else public_key_pem
    return serialization.load_pem_public_key(pem_bytes)


def _decode_signature_bytes(sig: str) -> bytes:
    try:
        return base64.b64decode(sig, validate=True)
    except Exception as exc:
        raise SignatureInvalidError("Signature is not valid base64.") from exc


def _as_der(sig_bytes: bytes) -> bytes:
    """Accept either DER-encoded ECDSA signatures or raw r||s (64 bytes) for P-256."""
    if len(sig_bytes) == 64:
        r = int.from_bytes(sig_bytes[:32], "big")
        s = int.from_bytes(sig_bytes[32:], "big")
        return encode_dss_signature(r, s)
    decode_dss_signature(sig_bytes)
    return sig_bytes


def verify_signature(
    public_key_pem: str,
    canonical: bytes,
    signature_b64: str,
) -> bool:
    if not signature_b64:
        return False
    try:
        pub = load_public_key(public_key_pem)
    except Exception as exc:
        raise SignatureInvalidError("Device public key is not a readable PEM.") from exc
    if not isinstance(pub, ec.EllipticCurvePublicKey):
        raise SignatureInvalidError("Device key is not an ECDSA public key.")
    raw = _decode_signature_bytes(signature_b64)
    try:
        der = _as_der(raw)
    except Exception as exc:
        raise SignatureInvalidError("Signature encoding is not recognized.") from exc
    try:
        pub.verify(der, canonical, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


def require_valid_signature(
    public_key_pem: str,
    canonical: bytes,
    signature_b64: str,
) -> None:
    if not verify_signature(public_key_pem, canonical, signature_b64):
        raise SignatureInvalidError("Request signature verification failed.")
