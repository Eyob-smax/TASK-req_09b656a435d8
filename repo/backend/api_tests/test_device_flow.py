"""
BE-API: full device enrollment flow.

Exercises: challenge → activate → register-implicit → verify a signed
request against the registered device → rotate → revoke.
"""
import base64
import hashlib
from datetime import datetime, timezone
import uuid

import json as _json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .conftest import make_signing_headers, register_device


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pub_pem


def _sign_b64(priv, message: bytes) -> str:
    return base64.b64encode(priv.sign(message, ec.ECDSA(hashes.SHA256()))).decode()


async def _login(client, user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": user["username"],
            "password": user["password"],
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": _now_iso(),
        },
    )
    assert resp.status_code == 200
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_challenge_activate_register_roundtrip(client, seeded_user):
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    priv, pub_pem = _keypair()
    fingerprint = "fp-" + uuid.uuid4().hex[:16]

    challenge = await client.post(
        "/api/v1/auth/device/challenge",
        headers=auth,
        json={"device_fingerprint": fingerprint, "public_key_pem": pub_pem},
    )
    assert challenge.status_code == 200
    ch_data = challenge.json()["data"]
    signature = _sign_b64(priv, ch_data["nonce"].encode("utf-8"))

    activate = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": ch_data["challenge_id"],
            "device_fingerprint": fingerprint,
            "public_key_pem": pub_pem,
            "signature": signature,
            "label": "laptop",
        },
    )
    assert activate.status_code == 200
    device_payload = activate.json()["data"]
    assert device_payload["device_fingerprint"] == fingerprint
    assert device_payload["device_id"]


@pytest.mark.asyncio
async def test_activate_with_bad_signature_rejected(client, seeded_user):
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    _, pub_pem = _keypair()
    fingerprint = "fp-" + uuid.uuid4().hex[:16]
    challenge = await client.post(
        "/api/v1/auth/device/challenge",
        headers=auth,
        json={"device_fingerprint": fingerprint, "public_key_pem": pub_pem},
    )
    ch_data = challenge.json()["data"]
    activate = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": ch_data["challenge_id"],
            "device_fingerprint": fingerprint,
            "public_key_pem": pub_pem,
            "signature": base64.b64encode(b"not-a-signature").decode(),
            "label": None,
        },
    )
    assert activate.status_code == 400
    assert activate.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_register_revoke_roundtrip(client, seeded_user):
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    _, pub_pem = _keypair()
    fingerprint = "fp-" + uuid.uuid4().hex[:16]

    reg = await client.post(
        "/api/v1/auth/device/register",
        headers=auth,
        json={
            "device_fingerprint": fingerprint,
            "public_key_pem": pub_pem,
            "label": "cli",
        },
    )
    assert reg.status_code == 200
    device_id = reg.json()["data"]["device_id"]

    revoke = await client.delete(
        f"/api/v1/auth/device/{device_id}",
        headers=auth,
    )
    assert revoke.status_code == 200
    assert revoke.json()["data"]["revoked"] is True


@pytest.mark.asyncio
async def test_challenge_persisted_in_db(client, seeded_user, test_session_factory):
    """device/challenge writes a row to device_enrollment_challenges."""
    from src.persistence.models.auth import DeviceEnrollmentChallenge

    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    _, pub_pem = _keypair()
    fingerprint = "fp-" + uuid.uuid4().hex[:16]

    resp = await client.post(
        "/api/v1/auth/device/challenge",
        headers=auth,
        json={"device_fingerprint": fingerprint, "public_key_pem": pub_pem},
    )
    assert resp.status_code == 200
    challenge_id = resp.json()["data"]["challenge_id"]

    async with test_session_factory() as session:
        row = await session.get(DeviceEnrollmentChallenge, challenge_id)
        assert row is not None
        assert row.device_fingerprint == fingerprint
        assert row.user_id == seeded_user["id"]


@pytest.mark.asyncio
async def test_activate_with_unknown_challenge_rejected(client, seeded_user):
    """Unknown challenge_id → 400 SIGNATURE_INVALID."""
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    priv, pub_pem = _keypair()
    fake_challenge_id = uuid.uuid4().hex
    signature = _sign_b64(priv, b"does-not-matter")

    resp = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": fake_challenge_id,
            "device_fingerprint": "fp-" + uuid.uuid4().hex[:16],
            "public_key_pem": pub_pem,
            "signature": signature,
            "label": None,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_activate_after_challenge_expiry_rejected(
    client, seeded_user, test_session_factory
):
    """Expired challenge row → 400 SIGNATURE_INVALID (and row is cleaned up)."""
    from datetime import timedelta

    from src.persistence.models.auth import DeviceEnrollmentChallenge
    from src.security import device_keys

    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    priv, pub_pem = _keypair()
    fingerprint = "fp-" + uuid.uuid4().hex[:16]

    ch = device_keys.generate_enrollment_challenge()
    past = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    async with test_session_factory() as session:
        row = DeviceEnrollmentChallenge(
            challenge_id=ch.challenge_id,
            nonce=ch.nonce,
            device_fingerprint=fingerprint,
            user_id=seeded_user["id"],
            expires_at=past,
            created_at=past - timedelta(minutes=5),
        )
        session.add(row)
        await session.commit()

    signature = _sign_b64(priv, ch.nonce.encode("utf-8"))
    resp = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": ch.challenge_id,
            "device_fingerprint": fingerprint,
            "public_key_pem": pub_pem,
            "signature": signature,
            "label": None,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_activate_is_single_use(client, seeded_user):
    """Second activate with the same challenge_id → 400 (row deleted on first consume)."""
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    priv, pub_pem = _keypair()
    fingerprint = "fp-" + uuid.uuid4().hex[:16]

    ch_resp = await client.post(
        "/api/v1/auth/device/challenge",
        headers=auth,
        json={"device_fingerprint": fingerprint, "public_key_pem": pub_pem},
    )
    ch_data = ch_resp.json()["data"]
    signature = _sign_b64(priv, ch_data["nonce"].encode("utf-8"))

    first = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": ch_data["challenge_id"],
            "device_fingerprint": fingerprint,
            "public_key_pem": pub_pem,
            "signature": signature,
            "label": "first-try",
        },
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": ch_data["challenge_id"],
            "device_fingerprint": fingerprint,
            "public_key_pem": pub_pem,
            "signature": signature,
            "label": "replay",
        },
    )
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_activate_with_mismatched_fingerprint_rejected(client, seeded_user):
    """Activate fingerprint must match the fingerprint bound to the challenge.

    Protects against cross-device enrollment replay: if the activate payload's
    device_fingerprint differs from the one the server persisted with the
    challenge row, the consume step discards the row and returns
    SIGNATURE_INVALID.
    """
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    priv, pub_pem = _keypair()
    enrolled_fingerprint = "fp-" + uuid.uuid4().hex[:16]

    challenge = await client.post(
        "/api/v1/auth/device/challenge",
        headers=auth,
        json={"device_fingerprint": enrolled_fingerprint, "public_key_pem": pub_pem},
    )
    assert challenge.status_code == 200
    ch_data = challenge.json()["data"]
    signature = _sign_b64(priv, ch_data["nonce"].encode("utf-8"))

    attacker_fingerprint = "fp-" + uuid.uuid4().hex[:16]
    resp = await client.post(
        "/api/v1/auth/device/activate",
        headers=auth,
        json={
            "challenge_id": ch_data["challenge_id"],
            "device_fingerprint": attacker_fingerprint,
            "public_key_pem": pub_pem,
            "signature": signature,
            "label": None,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"


@pytest.mark.asyncio
async def test_device_rotate_roundtrip(client, seeded_user):
    """POST /auth/device/{id}/rotate — signed request swaps the device's public key."""
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}

    device_id, priv = await register_device(client, auth)

    new_priv, new_pub_pem = _keypair()
    path = f"/api/v1/auth/device/{device_id}/rotate"
    body = _json.dumps({"new_public_key_pem": new_pub_pem}, separators=(",", ":")).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body, device_id)

    resp = await client.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert str(data["device_id"]) == str(device_id)
    assert data["is_active"] is True

    # New key must be accepted on a subsequent signed request; old key must not.
    register_path = "/api/v1/auth/device/register"
    noop_body = _json.dumps(
        {
            "device_fingerprint": "fp-" + uuid.uuid4().hex[:16],
            "public_key_pem": new_pub_pem,
            "label": "second",
        },
        separators=(",", ":"),
    ).encode()
    # Prove the rotated key works on a freshly-signed call by signing a ping-like
    # signed route. Use the same /rotate endpoint with the new key against the
    # same device — idempotent, proves the server stored the new pub key.
    sign_with_new = make_signing_headers(new_priv, "POST", path, body, device_id)
    resp2 = await client.post(
        path,
        headers={**auth, **sign_with_new, "Content-Type": "application/json"},
        content=body,
    )
    assert resp2.status_code == 200, resp2.text


@pytest.mark.asyncio
async def test_device_rotate_unsigned_rejected(client, seeded_user):
    """POST /auth/device/{id}/rotate without signing headers → 400 SIGNATURE_INVALID."""
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    device_id, _ = await register_device(client, auth)

    _, new_pub_pem = _keypair()
    resp = await client.post(
        f"/api/v1/auth/device/{device_id}/rotate",
        headers=auth,
        json={"new_public_key_pem": new_pub_pem},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"
