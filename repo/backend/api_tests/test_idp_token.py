"""
BE-API: POST /api/v1/idp/token.

Exercises client_credentials grant: unknown client rejected; valid client
receives a JWT signed with the same key advertised via JWKS.
"""
import uuid

import pytest
from jose import jwt as jose_jwt


@pytest.mark.asyncio
async def test_unknown_client_returns_auth_required(client):
    resp = await client.post(
        "/api/v1/idp/token",
        json={
            "client_id": "no-such-client",
            "client_secret": "nope",
            "grant_type": "client_credentials",
            "scope": "read",
        },
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_valid_client_issues_verifiable_token(client, test_session_factory):
    from src.persistence.models.auth import IdpClient
    from src.security.passwords import hash_password

    client_id = f"idp-{uuid.uuid4().hex[:8]}"
    client_secret = "a-very-long-client-secret"
    async with test_session_factory() as s:
        s.add(
            IdpClient(
                client_id=client_id,
                client_secret_hash=hash_password(client_secret),
                name="Internal Report Worker",
                allowed_scopes="read:reports",
                is_active=True,
            )
        )
        await s.commit()

    resp = await client.post(
        "/api/v1/idp/token",
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "read:reports",
        },
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]

    # Fetch JWKS and verify with the advertised public key
    jwks_resp = await client.get("/api/v1/idp/jwks")
    assert jwks_resp.status_code == 200
    jwks = jwks_resp.json()
    # Use python-jose to verify the token against the JWKS
    claims = jose_jwt.decode(
        token,
        jwks,
        algorithms=["RS256"],
        audience="internal",
        issuer="merittrack",
    )
    assert claims["client_id"] == client_id
    assert "read:reports" in claims["scope"].split()


@pytest.mark.asyncio
async def test_wrong_secret_returns_auth_required(client, test_session_factory):
    from src.persistence.models.auth import IdpClient
    from src.security.passwords import hash_password

    client_id = f"idp-{uuid.uuid4().hex[:8]}"
    async with test_session_factory() as s:
        s.add(
            IdpClient(
                client_id=client_id,
                client_secret_hash=hash_password("right-secret-long-enough"),
                name="x",
                allowed_scopes="read",
                is_active=True,
            )
        )
        await s.commit()

    resp = await client.post(
        "/api/v1/idp/token",
        json={
            "client_id": client_id,
            "client_secret": "wrong-secret-long-enough",
            "grant_type": "client_credentials",
            "scope": "read",
        },
    )
    assert resp.status_code == 401
