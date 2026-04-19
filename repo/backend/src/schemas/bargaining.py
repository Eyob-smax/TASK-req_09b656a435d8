import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ..domain.enums import BargainingStatus, BargainingOfferOutcome


class OfferCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Proposed price; must be positive.")
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)


class OfferRead(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    offer_number: int
    amount: Decimal
    submitted_by: uuid.UUID
    submitted_at: datetime
    outcome: BargainingOfferOutcome | None


class CounterCreate(BaseModel):
    counter_amount: Decimal = Field(..., gt=0)
    notes: str | None = Field(None, max_length=1000)


class BargainingAcceptRequest(BaseModel):
    offer_id: uuid.UUID
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)


class CounterAcceptRequest(BaseModel):
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)


class BargainingThreadRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    status: BargainingStatus
    window_starts_at: datetime
    window_expires_at: datetime
    counter_count: int
    counter_amount: Decimal | None
    counter_at: datetime | None
    resolved_at: datetime | None
    offers: list[OfferRead] = []
