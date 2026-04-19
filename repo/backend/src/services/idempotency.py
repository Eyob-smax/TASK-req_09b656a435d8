"""
Idempotency service.

Mutating endpoints accept an `Idempotency-Key` header. The first response
is persisted with its request-body hash and response envelope; subsequent
calls with the same key + method + path return the cached envelope verbatim.
If the request body differs from the originally stored hash, an
`IdempotencyConflictError` is raised (per RFC 9457-style semantics).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..persistence.models.idempotency import IdempotencyKey
from ..persistence.repositories.idempotency_repo import IdempotencyRepository
from ..security.errors import IdempotencyConflictError


@dataclass
class CachedResponse:
    status_code: int
    body: Any


def hash_request_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


class IdempotencyStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = IdempotencyRepository(session)
        self.settings = get_settings()

    async def fetch(
        self,
        *,
        key: str,
        method: str,
        path: str,
        request_body: bytes,
    ) -> CachedResponse | None:
        row = await self.repo.get(key=key, method=method, path=path)
        if row is None:
            return None
        now = datetime.now(tz=timezone.utc)
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            return None
        if row.request_hash != hash_request_body(request_body):
            raise IdempotencyConflictError(
                "Idempotency-Key reused with a different request body."
            )
        try:
            body = json.loads(row.response_body) if row.response_body else None
        except json.JSONDecodeError:
            body = row.response_body
        return CachedResponse(status_code=row.response_status, body=body)

    async def store(
        self,
        *,
        key: str,
        method: str,
        path: str,
        actor_id: uuid.UUID | None,
        request_body: bytes,
        response_status: int,
        response_body: Any,
    ) -> IdempotencyKey:
        body_str = json.dumps(response_body, default=str) if response_body is not None else ""
        expires = datetime.now(tz=timezone.utc) + timedelta(
            hours=self.settings.idempotency_key_ttl_hours
        )
        return await self.repo.insert(
            key=key,
            method=method,
            path=path,
            actor_id=actor_id,
            request_hash=hash_request_body(request_body),
            response_status=response_status,
            response_body=body_str,
            expires_at=expires,
        )

    async def purge_expired(self) -> int:
        return await self.repo.purge_expired(now=datetime.now(tz=timezone.utc))
