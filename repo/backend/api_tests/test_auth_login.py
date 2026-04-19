"""
BE-API: POST /api/v1/auth/login.

Covers:
    * happy path → 200 + TokenResponse envelope
    * wrong password → AUTH_REQUIRED (401)
    * short password → VALIDATION_ERROR (422)
    * missing username → VALIDATION_ERROR (422)
"""
from datetime import datetime, timezone
import uuid

import pytest


def _signed_payload(username: str, password: str) -> dict:
    return {
        "username": username,
        "password": password,
        "nonce": f"n-{uuid.uuid4().hex}",
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@pytest.mark.asyncio
async def test_login_happy_path(client, seeded_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json=_signed_payload(seeded_user["username"], seeded_user["password"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["role"] == "candidate"
    assert data["expires_in"] == 15 * 60


@pytest.mark.asyncio
async def test_login_wrong_password_returns_auth_required(client, seeded_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json=_signed_payload(seeded_user["username"], "wrong-passwordxxx"),
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_login_short_password_rejected_by_schema(client, seeded_user):
    payload = _signed_payload(seeded_user["username"], "short")
    resp = await client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_login_missing_username_rejected(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "password": "correct horse battery staple",
            "nonce": "nnn-12345",
            "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_unknown_user_returns_auth_required(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json=_signed_payload("no-such-user-xyz", "correct horse battery staple"),
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_login_throttled_after_repeated_failures(client, seeded_user):
    # 5 failed attempts → 6th should be throttled (HTTP 429 AUTH_THROTTLED)
    for _ in range(5):
        bad = await client.post(
            "/api/v1/auth/login",
            json=_signed_payload(seeded_user["username"], "wrong-passwordxxx"),
        )
        assert bad.status_code == 401
    final = await client.post(
        "/api/v1/auth/login",
        json=_signed_payload(seeded_user["username"], "wrong-passwordxxx"),
    )
    assert final.status_code == 429
    assert final.json()["error"]["code"] == "AUTH_THROTTLED"
