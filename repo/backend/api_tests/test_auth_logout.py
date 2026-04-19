"""
BE-API: POST /api/v1/auth/logout.

Successful logout invalidates the refresh-token family so subsequent
refresh attempts return AUTH_REQUIRED.
"""
from datetime import datetime, timezone
import uuid

import pytest


def _signed(body: dict) -> dict:
    body.setdefault("nonce", f"n-{uuid.uuid4().hex}")
    body.setdefault(
        "timestamp",
        datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    return body


async def _login(client, user):
    resp = await client.post(
        "/api/v1/auth/login",
        json=_signed({"username": user["username"], "password": user["password"]}),
    )
    assert resp.status_code == 200
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_logout_invalidates_family(client, seeded_user):
    tokens = await _login(client, seeded_user)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 200

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json=_signed({"refresh_token": tokens["refresh_token"]}),
    )
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_without_auth_rejected(client, seeded_user):
    tokens = await _login(client, seeded_user)
    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_REQUIRED"
