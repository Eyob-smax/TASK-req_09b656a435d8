"""
BE-API: POST /api/v1/auth/password/change.

Route requires an authenticated signed request. All tests supply real
ECDSA signing headers (no bypass). Happy-path flow is also covered in
test_signed_route_success.py.
"""
from datetime import datetime, timezone
import json
import uuid

import pytest

from .conftest import make_signing_headers, register_device


async def _login(client, user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": user["username"],
            "password": user["password"],
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_password_change_schema_rejects_short_new(client, seeded_user):
    tokens = await _login(client, seeded_user)
    auth = {"Authorization": f"Bearer {tokens['access_token']}"}
    device_id, priv = await register_device(client, auth)
    path = "/api/v1/auth/password/change"
    body_dict = {
        "current_password": seeded_user["password"],
        "new_password": "too-short",
        "nonce": f"n-{uuid.uuid4().hex}",
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    body_bytes = json.dumps(body_dict, separators=(",", ":")).encode()
    sign_hdrs = make_signing_headers(priv, "POST", path, body_bytes, device_id)
    resp = await client.post(
        path,
        headers={**auth, **sign_hdrs, "Content-Type": "application/json"},
        content=body_bytes,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_password_change_requires_authentication(client):
    resp = await client.post(
        "/api/v1/auth/password/change",
        json={
            "current_password": "irrelevant1234",
            "new_password": "new-correct-horse-battery",
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_password_change_requires_signature_headers(client, seeded_user):
    tokens = await _login(client, seeded_user)
    resp = await client.post(
        "/api/v1/auth/password/change",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "current_password": seeded_user["password"],
            "new_password": "new-correct-horse-battery",
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    # No X-Signature / X-Nonce / X-Device-ID headers supplied → SIGNATURE_INVALID
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"
