"""
Device-enrollment challenge flow.
"""
import base64

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from src.security import device_keys
from src.security.errors import SignatureInvalidError


def _keypair_and_pem() -> tuple[ec.EllipticCurvePrivateKey, str]:
    priv = ec.generate_private_key(ec.SECP256R1())
    pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pem


def test_challenge_is_unique():
    a = device_keys.generate_enrollment_challenge()
    b = device_keys.generate_enrollment_challenge()
    assert a.challenge_id != b.challenge_id
    assert a.nonce != b.nonce


def test_activation_signature_verifies():
    challenge = device_keys.generate_enrollment_challenge()
    priv, pem = _keypair_and_pem()
    der = priv.sign(challenge.nonce.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    sig = base64.b64encode(der).decode()
    assert device_keys.verify_enrollment_signature(
        challenge_nonce=challenge.nonce, signature_b64=sig, public_key_pem=pem
    )


def test_activation_wrong_key_fails():
    challenge = device_keys.generate_enrollment_challenge()
    _, pem = _keypair_and_pem()
    other_priv, _ = _keypair_and_pem()
    der = other_priv.sign(challenge.nonce.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    sig = base64.b64encode(der).decode()
    assert device_keys.verify_enrollment_signature(
        challenge_nonce=challenge.nonce, signature_b64=sig, public_key_pem=pem
    ) is False


def test_import_rejects_non_ec_pem():
    # Simulate RSA-shaped key being handed over as a device key.
    from cryptography.hazmat.primitives.asymmetric import rsa

    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pem = rsa_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    with pytest.raises(SignatureInvalidError):
        device_keys.import_spki_pem(rsa_pem)


def test_import_rejects_junk():
    with pytest.raises(SignatureInvalidError):
        device_keys.import_spki_pem("not a pem")
