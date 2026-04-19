from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.idempotency import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(
        self, *, key: str, method: str, path: str
    ) -> IdempotencyKey | None:
        q = select(IdempotencyKey).where(
            IdempotencyKey.key == key,
            IdempotencyKey.method == method.upper(),
            IdempotencyKey.path == path,
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def insert(
        self,
        *,
        key: str,
        method: str,
        path: str,
        actor_id: uuid.UUID | None,
        request_hash: str,
        response_status: int,
        response_body: str,
        expires_at: datetime,
    ) -> IdempotencyKey:
        row = IdempotencyKey(
            key=key,
            method=method.upper(),
            path=path,
            actor_id=actor_id,
            request_hash=request_hash,
            response_status=response_status,
            response_body=response_body,
            expires_at=expires_at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def purge_expired(self, *, now: datetime) -> int:
        stmt = delete(IdempotencyKey).where(IdempotencyKey.expires_at < now)
        res = await self.session.execute(stmt)
        return res.rowcount or 0
