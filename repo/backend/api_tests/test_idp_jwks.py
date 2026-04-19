"""
BE-API-MOCK: GET /api/v1/idp/jwks.

Exercises ASGI transport against the real app; the JWKS response is
served from the installed signing key pair (injected by the
`_install_jwt_keys` fixture) so no database or external state is read.
"""
import pytest


@pytest.mark.asyncio
async def test_jwks_is_well_formed(client):
    resp = await client.get("/api/v1/idp/jwks")
    assert resp.status_code == 200
    body = resp.json()
    assert "keys" in body and len(body["keys"]) == 1
    key = body["keys"][0]
    assert key["kty"] == "RSA"
    assert key["alg"] == "RS256"
    assert key["use"] == "sig"
    assert key["kid"]
    assert key["n"]
    assert key["e"]


@pytest.mark.asyncio
async def test_jwks_has_no_private_material(client):
    resp = await client.get("/api/v1/idp/jwks")
    body = resp.json()
    key = body["keys"][0]
    for forbidden in ("d", "p", "q", "dp", "dq", "qi"):
        assert forbidden not in key, (
            f"JWKS response must not expose RSA private component '{forbidden}'"
        )
