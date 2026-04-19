"""
Device enrollment challenge / activation.

Challenge is a server-generated opaque nonce. The frontend signs it with the
newly-generated device private key; the backend verifies using the SPKI PEM
sent up alongside. After a successful activation, the device registration
record stores the public key for subsequent request-signature verification.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .errors import SignatureInvalidError
from .signing import verify_signature

CHALLENGE_BYTES = 32


@dataclass(frozen=True)
class DeviceChallenge:
    challenge_id: str
    nonce: str  # signed by the device during activation


def generate_enrollment_challenge() -> DeviceChallenge:
    return DeviceChallenge(
        challenge_id=secrets.token_urlsafe(16),
        nonce=secrets.token_urlsafe(CHALLENGE_BYTES),
    )


def import_spki_pem(public_key_pem: str) -> ec.EllipticCurvePublicKey:
    try:
        pub = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    except Exception as exc:
        raise SignatureInvalidError("Device public key is not a readable PEM.") from exc
    if not isinstance(pub, ec.EllipticCurvePublicKey):
        raise SignatureInvalidError("Device key must be ECDSA (P-256).")
    return pub


def verify_enrollment_signature(
    *,
    challenge_nonce: str,
    signature_b64: str,
    public_key_pem: str,
) -> bool:
    canonical = challenge_nonce.encode("utf-8")
    return verify_signature(public_key_pem, canonical, signature_b64)
