"""BE-API: /api/v1/internal/metrics admin-only authorization."""
from __future__ import annotations

import pytest

from .conftest import login


@pytest.mark.asyncio
async def test_metrics_requires_auth(client):
    """No token → 401 AUTH_REQUIRED."""
    resp = await client.get("/api/v1/internal/metrics")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_metrics_forbids_candidate(client, seeded_user):
    """Candidate JWT → 403 FORBIDDEN."""
    cand_token = await login(client, seeded_user)
    resp = await client.get(
        "/api/v1/internal/metrics",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_metrics_forbids_reviewer(client, seeded_reviewer):
    """Reviewer JWT → 403 FORBIDDEN (metrics is admin-only)."""
    rev_token = await login(client, seeded_reviewer)
    resp = await client.get(
        "/api/v1/internal/metrics",
        headers={"Authorization": f"Bearer {rev_token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_metrics_admin_ok(client, seeded_admin):
    """Admin JWT → 200 with Prometheus text exposition."""
    admin_token = await login(client, seeded_admin)
    resp = await client.get(
        "/api/v1/internal/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "# HELP" in body or "# TYPE" in body
