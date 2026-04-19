import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from ..domain.enums import DocumentStatus, ExceptionStatus, OrderStatus, ReviewStage


class DocumentQueueItem(BaseModel):
    document_id: uuid.UUID
    candidate_id: uuid.UUID
    document_type: str
    current_status: DocumentStatus
    requirement_code: str | None
    updated_at: datetime


class PaymentQueueItem(BaseModel):
    order_id: uuid.UUID
    candidate_id: uuid.UUID
    item_name: str
    amount: Decimal
    payment_method: str
    reference_number: str | None
    submitted_at: datetime


class OrderQueueItem(BaseModel):
    order_id: uuid.UUID
    candidate_id: uuid.UUID
    item_name: str
    status: OrderStatus
    agreed_price: Decimal | None
    updated_at: datetime


class ExceptionQueueItem(BaseModel):
    exception_id: uuid.UUID
    candidate_id: uuid.UUID
    status: ExceptionStatus
    current_stage: ReviewStage
    submitted_at: datetime | None
    created_at: datetime


class AfterSalesQueueItem(BaseModel):
    request_id: uuid.UUID
    order_id: uuid.UUID
    candidate_id: uuid.UUID
    request_type: str
    status: str
    window_expires_at: datetime
    created_at: datetime
