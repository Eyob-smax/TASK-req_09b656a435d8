"""
BE-API-MOCK: verify that error envelopes never leak secrets or stack traces.

Covers:
    * unhandled exception path does not leak the exception type / traceback
    * signature-invalid responses do not echo the offending header values
    * validation errors do not echo submitted password fields
"""
from datetime import datetime, timezone
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.errors import register_exception_handlers


@pytest_asyncio.fixture
async def error_client(_install_jwt_keys):
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("ultra-secret internal detail: TOKEN=abcdefg")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_unhandled_exception_does_not_leak_details(error_client):
    resp = await error_client.get("/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "ultra-secret" not in resp.text
    assert "abcdefg" not in resp.text
    assert "Traceback" not in resp.text
    assert "RuntimeError" not in resp.text


@pytest.mark.asyncio
async def test_validation_error_does_not_echo_password(client):
    payload = {
        "username": "a",
        "password": "tiny",  # schema enforces min_length=12
        "nonce": "n-abcdef12",
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    resp = await client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 422
    assert "tiny" not in resp.text


@pytest.mark.asyncio
async def test_signature_invalid_does_not_echo_body(client, seeded_user):
    # Log in first
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": seeded_user["username"],
            "password": seeded_user["password"],
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    access = login.json()["data"]["access_token"]
    # Hit a signed route without signing headers; body contains markers
    resp = await client.post(
        "/api/v1/auth/password/change",
        headers={"Authorization": f"Bearer {access}"},
        json={
            "current_password": "MARKER-CURRENT-PASSWORD-LEAK",
            "new_password": "MARKER-NEW-PASSWORD-LEAK-LONG",
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SIGNATURE_INVALID"
    assert "MARKER-CURRENT-PASSWORD-LEAK" not in resp.text
    assert "MARKER-NEW-PASSWORD-LEAK-LONG" not in resp.text
