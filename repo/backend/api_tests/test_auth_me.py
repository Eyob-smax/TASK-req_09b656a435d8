"""
BE-API: GET /api/v1/auth/me.

Covers authenticated happy-path and missing-auth rejection.
"""
from datetime import datetime, timezone
import uuid

import pytest


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
    assert resp.status_code == 200
    return resp.json()["data"]


@pytest.mark.asyncio
async def test_me_returns_profile_for_authenticated_user(client, seeded_user):
    tokens = await _login(client, seeded_user)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    user_payload = body["data"]["user"]
    assert user_payload["username"] == seeded_user["username"]
    assert user_payload["role"] == "candidate"


@pytest.mark.asyncio
async def test_me_requires_authentication(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_me_rejects_invalid_bearer(client):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_candidate_id_for_candidate(
    client, seeded_user, seeded_reviewer
):
    """After a candidate profile exists, /auth/me surfaces its candidate_id
    (distinct from user.id). Required for FE to call candidate-scoped routes
    without guessing user.id == profile.id."""
    rev_tokens = await _login(client, seeded_reviewer)
    create_resp = await client.post(
        "/api/v1/candidates",
        params={"user_id": str(seeded_user["id"])},
        headers={"Authorization": f"Bearer {rev_tokens['access_token']}"},
    )
    assert create_resp.status_code in (200, 201, 409), create_resp.text
    # Re-fetch candidate profile to obtain its actual id regardless of path taken.
    if create_resp.status_code in (200, 201):
        candidate_id = create_resp.json()["data"]["id"]
    else:
        list_resp = await client.get(
            "/api/v1/candidates",
            headers={"Authorization": f"Bearer {rev_tokens['access_token']}"},
        )
        assert list_resp.status_code == 200
        match = next(
            p for p in list_resp.json()["data"] if p["user_id"] == str(seeded_user["id"])
        )
        candidate_id = match["id"]

    cand_tokens = await _login(client, seeded_user)
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {cand_tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    body = me_resp.json()["data"]
    assert body["candidate_id"] == candidate_id
    assert body["user"]["id"] == str(seeded_user["id"])
    # candidate_id must NOT equal user.id — they are different entities.
    assert body["candidate_id"] != body["user"]["id"]


@pytest.mark.asyncio
async def test_me_candidate_id_null_for_non_candidate(client, seeded_reviewer):
    """Non-candidate roles (reviewer/admin/proctor) receive candidate_id=null."""
    tokens = await _login(client, seeded_reviewer)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["candidate_id"] is None
    assert body["user"]["role"] == "reviewer"


@pytest.mark.asyncio
async def test_me_candidate_id_null_when_profile_missing(client, seeded_user):
    """Candidate user without a CandidateProfile row receives candidate_id=null
    rather than 500ing — FE shows 'contact staff' banner."""
    tokens = await _login(client, seeded_user)
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    # No profile has been created for seeded_user in this test — so null.
    assert body["candidate_id"] is None
