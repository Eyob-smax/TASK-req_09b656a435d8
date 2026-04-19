"""
IdempotencyStore semantics: body hashing, cache-hit equality, conflict on body mismatch.

DB interactions are stubbed with a small in-memory fake to keep this file a
pure unit test; integration coverage of the real table lives under api_tests/.
"""
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from src.security.errors import IdempotencyConflictError
from src.services.idempotency import IdempotencyStore, hash_request_body


class _FakeRepo:
    def __init__(self):
        self._rows: dict[tuple[str, str, str], object] = {}

    async def get(self, *, key, method, path):
        return self._rows.get((key, method.upper(), path))

    async def insert(self, **kwargs):
        from types import SimpleNamespace

        payload = dict(kwargs)
        payload["method"] = kwargs["method"].upper()
        row = SimpleNamespace(
            id=uuid.uuid4(),
            created_at=datetime.now(tz=timezone.utc),
            **payload,
        )
        self._rows[(kwargs["key"], kwargs["method"].upper(), kwargs["path"])] = row
        return row

    async def purge_expired(self, *, now):
        purged = 0
        for k in list(self._rows.keys()):
            if self._rows[k].expires_at <= now:
                del self._rows[k]
                purged += 1
        return purged


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://test:test@localhost/test")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)


@pytest.mark.asyncio
async def test_body_hash_deterministic():
    a = hash_request_body(b'{"x":1}')
    b = hash_request_body(b'{"x":1}')
    assert a == b
    assert a != hash_request_body(b'{"x":2}')


@pytest.mark.asyncio
async def test_store_and_fetch_cached_response():
    store = IdempotencyStore(session=None)  # type: ignore[arg-type]
    store.repo = _FakeRepo()  # type: ignore[assignment]
    await store.store(
        key="idem-00000001",
        method="POST",
        path="/api/v1/orders",
        actor_id=None,
        request_body=b'{"x":1}',
        response_status=201,
        response_body={"ok": True},
    )
    cached = await store.fetch(
        key="idem-00000001",
        method="POST",
        path="/api/v1/orders",
        request_body=b'{"x":1}',
    )
    assert cached is not None
    assert cached.status_code == 201
    assert cached.body == {"ok": True}


@pytest.mark.asyncio
async def test_conflict_on_body_mismatch():
    store = IdempotencyStore(session=None)  # type: ignore[arg-type]
    store.repo = _FakeRepo()  # type: ignore[assignment]
    await store.store(
        key="idem-00000002",
        method="POST",
        path="/api/v1/orders",
        actor_id=None,
        request_body=b'{"x":1}',
        response_status=201,
        response_body={"ok": True},
    )
    with pytest.raises(IdempotencyConflictError):
        await store.fetch(
            key="idem-00000002",
            method="POST",
            path="/api/v1/orders",
            request_body=b'{"x":2}',
        )


@pytest.mark.asyncio
async def test_expired_entry_returns_none():
    store = IdempotencyStore(session=None)  # type: ignore[arg-type]
    repo = _FakeRepo()
    store.repo = repo  # type: ignore[assignment]
    await store.store(
        key="idem-expired00",
        method="POST",
        path="/api/v1/orders",
        actor_id=None,
        request_body=b'{}',
        response_status=200,
        response_body={},
    )
    # Force the cached expiry into the past
    entry = list(repo._rows.values())[0]
    entry.expires_at = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    result = await store.fetch(
        key="idem-expired00",
        method="POST",
        path="/api/v1/orders",
        request_body=b'{}',
    )
    assert result is None


@pytest.mark.asyncio
async def test_missing_key_returns_none():
    store = IdempotencyStore(session=None)  # type: ignore[arg-type]
    store.repo = _FakeRepo()  # type: ignore[assignment]
    assert await store.fetch(
        key="never-stored-123",
        method="POST",
        path="/api/v1/orders",
        request_body=b'{}',
    ) is None
