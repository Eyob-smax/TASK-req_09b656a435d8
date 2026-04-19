from __future__ import annotations

from pydantic import BaseModel, Field


class IdempotencyKeyHeader(BaseModel):
    """Describes the Idempotency-Key header value accepted on mutating routes."""

    idempotency_key: str = Field(..., min_length=8, max_length=128)
