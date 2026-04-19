import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ..domain.enums import OrderStatus, PricingMode


class ServiceItemRead(BaseModel):
    id: uuid.UUID
    item_code: str
    name: str
    description: str | None
    pricing_mode: PricingMode
    fixed_price: Decimal | None
    is_capacity_limited: bool
    bargaining_enabled: bool
    available_slots: int | None = None


class OrderCreate(BaseModel):
    item_id: uuid.UUID
    pricing_mode: PricingMode
    idempotency_key: str | None = Field(None, max_length=64)


class OrderEventRead(BaseModel):
    id: uuid.UUID
    sequence_number: int
    event_type: str
    previous_state: OrderStatus | None
    new_state: OrderStatus
    actor_id: uuid.UUID | None
    actor_role: str | None
    notes: str | None
    occurred_at: datetime


class OrderRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    item_id: uuid.UUID
    status: OrderStatus
    pricing_mode: PricingMode
    agreed_price: Decimal | None
    auto_cancel_at: datetime | None
    completed_at: datetime | None
    canceled_at: datetime | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
    events: list[OrderEventRead] = []


class PaymentConfirmRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., max_length=50)
    reference_number: str | None = Field(None, max_length=200)
    notes: str | None = None


class VoucherRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    voucher_code: str
    issued_by: uuid.UUID
    issued_at: datetime
    notes: str | None


class MilestoneCreate(BaseModel):
    milestone_type: str = Field(..., max_length=100)
    description: str | None = None


class MilestoneRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    milestone_type: str
    description: str | None
    recorded_by: uuid.UUID
    occurred_at: datetime


class RefundCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=2000)


class RefundRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    amount: Decimal
    initiated_by: uuid.UUID
    initiated_at: datetime
    processed_by: uuid.UUID | None
    processed_at: datetime | None
    reason: str
    rollback_applied: bool


class PaymentProofSubmit(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., max_length=50)
    reference_number: str | None = Field(None, max_length=200)
    notes: str | None = None


class VoucherCreate(BaseModel):
    notes: str | None = Field(None, max_length=1000)


class OrderTransitionRequest(BaseModel):
    notes: str | None = Field(None, max_length=500)


class AfterSalesRequestCreate(BaseModel):
    request_type: str = Field(..., max_length=100)
    description: str = Field(..., min_length=1, max_length=5000)


class AfterSalesRequestRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    requested_by: uuid.UUID
    request_type: str
    description: str
    status: str
    window_expires_at: datetime
    resolved_by: uuid.UUID | None
    resolved_at: datetime | None
    resolution_notes: str | None
    created_at: datetime


class AfterSalesResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=1, max_length=5000)
