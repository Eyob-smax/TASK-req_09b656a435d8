from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.enums import DocumentStatus, ExceptionStatus, OrderStatus, ReviewStage
from ..persistence.models.attendance import AttendanceException
from ..persistence.models.document import Document
from ..persistence.models.order import AfterSalesRequest, Order, PaymentRecord, ServiceItem
from ..schemas.queue import (
    AfterSalesQueueItem,
    DocumentQueueItem,
    ExceptionQueueItem,
    OrderQueueItem,
    PaymentQueueItem,
)


class QueueService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def pending_documents(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[DocumentQueueItem], int]:
        pending_statuses = [
            DocumentStatus.pending_review.value,
            DocumentStatus.needs_resubmission.value,
        ]
        q = select(Document).where(Document.current_status.in_(pending_statuses))
        total = (
            await self._session.execute(
                select(func.count()).select_from(q.subquery())
            )
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        docs = list((await self._session.execute(q)).scalars().all())
        return (
            [
                DocumentQueueItem(
                    document_id=d.id,
                    candidate_id=d.candidate_id,
                    document_type=d.document_type,
                    current_status=DocumentStatus(d.current_status),
                    requirement_code=None,
                    updated_at=d.updated_at,
                )
                for d in docs
            ],
            total,
        )

    async def pending_payments(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[PaymentQueueItem], int]:
        q = (
            select(PaymentRecord)
            .options(selectinload(PaymentRecord.order).selectinload(Order.item))
            .where(PaymentRecord.confirmed_by.is_(None))
        )
        total = (
            await self._session.execute(
                select(func.count()).select_from(q.subquery())
            )
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        records = list((await self._session.execute(q)).scalars().all())
        items = []
        for r in records:
            order = r.order
            item = order.item if order else None
            items.append(
                PaymentQueueItem(
                    order_id=r.order_id,
                    candidate_id=order.candidate_id if order else uuid.UUID(int=0),
                    item_name=item.name if item else "",
                    amount=r.amount,
                    payment_method=r.payment_method,
                    reference_number=r.reference_number,
                    submitted_at=r.created_at,
                )
            )
        return items, total

    async def pending_orders(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[OrderQueueItem], int]:
        q = (
            select(Order)
            .options(selectinload(Order.item))
            .where(Order.status == OrderStatus.pending_fulfillment.value)
        )
        total = (
            await self._session.execute(
                select(func.count()).select_from(q.subquery())
            )
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        orders = list((await self._session.execute(q)).scalars().all())
        return (
            [
                OrderQueueItem(
                    order_id=o.id,
                    candidate_id=o.candidate_id,
                    item_name=o.item.name if o.item else "",
                    status=OrderStatus(o.status),
                    agreed_price=o.agreed_price,
                    updated_at=o.updated_at,
                )
                for o in orders
            ],
            total,
        )

    async def pending_exceptions(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[ExceptionQueueItem], int]:
        review_statuses = [
            ExceptionStatus.pending_initial_review.value,
            ExceptionStatus.pending_final_review.value,
        ]
        q = select(AttendanceException).where(
            AttendanceException.status.in_(review_statuses)
        )
        if status:
            q = select(AttendanceException).where(
                AttendanceException.status == status
            )
        total = (
            await self._session.execute(
                select(func.count()).select_from(q.subquery())
            )
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        exceptions = list((await self._session.execute(q)).scalars().all())
        return (
            [
                ExceptionQueueItem(
                    exception_id=e.id,
                    candidate_id=e.candidate_id,
                    status=ExceptionStatus(e.status),
                    current_stage=ReviewStage(e.current_stage),
                    submitted_at=e.submitted_at,
                    created_at=e.created_at,
                )
                for e in exceptions
            ],
            total,
        )

    async def pending_after_sales(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[AfterSalesQueueItem], int]:
        q = select(AfterSalesRequest).where(AfterSalesRequest.status == "open")
        total = (
            await self._session.execute(
                select(func.count()).select_from(q.subquery())
            )
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        requests = list((await self._session.execute(q)).scalars().all())
        return (
            [
                AfterSalesQueueItem(
                    request_id=r.id,
                    order_id=r.order_id,
                    candidate_id=r.requested_by,
                    request_type=r.request_type,
                    status=r.status,
                    window_expires_at=r.window_expires_at,
                    created_at=r.created_at,
                )
                for r in requests
            ],
            total,
        )
