from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.order import (
    AfterSalesRequest,
    BargainingOffer,
    BargainingThread,
    FulfillmentMilestone,
    Order,
    OrderEvent,
    PaymentRecord,
    RefundRecord,
    RollbackEvent,
    ServiceItem,
    ServiceItemInventory,
    Voucher,
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Service catalog ───────────────────────────────────────────────────────

    async def get_service_item(self, item_id: uuid.UUID) -> ServiceItem | None:
        q = (
            select(ServiceItem)
            .options(selectinload(ServiceItem.inventory))
            .where(ServiceItem.id == item_id)
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_service_items(self) -> list[ServiceItem]:
        q = (
            select(ServiceItem)
            .options(selectinload(ServiceItem.inventory))
            .where(ServiceItem.is_active.is_(True))
        )
        return list((await self.session.execute(q)).scalars().all())

    # ── Inventory (concurrency-safe) ──────────────────────────────────────────

    async def lock_inventory(
        self, item_id: uuid.UUID
    ) -> ServiceItemInventory | None:
        q = (
            select(ServiceItemInventory)
            .where(ServiceItemInventory.item_id == item_id)
            .with_for_update()
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def reserve_slot(self, inventory: ServiceItemInventory) -> None:
        inventory.reserved_count += 1
        await self.session.flush()

    async def release_slot(self, inventory: ServiceItemInventory) -> None:
        if inventory.reserved_count > 0:
            inventory.reserved_count -= 1
        await self.session.flush()

    # ── Orders ────────────────────────────────────────────────────────────────

    async def get_order(self, order_id: uuid.UUID) -> Order | None:
        q = (
            select(Order)
            .options(
                selectinload(Order.events),
                selectinload(Order.bargaining_thread).selectinload(
                    BargainingThread.offers
                ),
                selectinload(Order.payment_record),
                selectinload(Order.item).selectinload(ServiceItem.inventory),
                selectinload(Order.voucher),
                selectinload(Order.milestones),
                selectinload(Order.refund_records),
                selectinload(Order.after_sales_requests),
            )
            .where(Order.id == order_id)
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_orders(
        self,
        candidate_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        q = select(Order).options(selectinload(Order.events))
        if candidate_id is not None:
            q = q.where(Order.candidate_id == candidate_id)
        if status is not None:
            q = q.where(Order.status == status)
        total = (
            await self.session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        orders = list((await self.session.execute(q)).scalars().all())
        return orders, total

    async def find_by_idempotency_key(self, key: str) -> Order | None:
        q = select(Order).where(Order.idempotency_key == key)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create_order(
        self,
        candidate_id: uuid.UUID,
        item_id: uuid.UUID,
        pricing_mode: str,
        auto_cancel_at: datetime,
        idempotency_key: str | None = None,
    ) -> Order:
        order = Order(
            candidate_id=candidate_id,
            item_id=item_id,
            status="pending_payment",
            pricing_mode=pricing_mode,
            auto_cancel_at=auto_cancel_at,
            idempotency_key=idempotency_key,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def append_event(
        self,
        order: Order,
        event_type: str,
        prev_state: str | None,
        new_state: str,
        actor_id: uuid.UUID | None,
        actor_role: str | None,
        notes: str | None = None,
    ) -> OrderEvent:
        seq = len(order.events) + 1 if order.events is not None else 1
        event = OrderEvent(
            order_id=order.id,
            sequence_number=seq,
            event_type=event_type,
            previous_state=prev_state,
            new_state=new_state,
            actor_id=actor_id,
            actor_role=actor_role,
            notes=notes,
            occurred_at=_now(),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def update_order_status(
        self, order: Order, new_status: str, **extra_fields
    ) -> None:
        order.status = new_status
        for key, value in extra_fields.items():
            setattr(order, key, value)
        await self.session.flush()

    # ── Bargaining ────────────────────────────────────────────────────────────

    async def get_thread(self, order_id: uuid.UUID) -> BargainingThread | None:
        q = (
            select(BargainingThread)
            .options(selectinload(BargainingThread.offers))
            .where(BargainingThread.order_id == order_id)
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create_thread(
        self,
        order_id: uuid.UUID,
        window_starts_at: datetime,
        window_expires_at: datetime,
    ) -> BargainingThread:
        thread = BargainingThread(
            order_id=order_id,
            status="open",
            window_starts_at=window_starts_at,
            window_expires_at=window_expires_at,
            counter_count=0,
        )
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def add_offer(
        self,
        thread: BargainingThread,
        offer_number: int,
        amount,
        submitted_by: uuid.UUID,
    ) -> BargainingOffer:
        offer = BargainingOffer(
            thread_id=thread.id,
            offer_number=offer_number,
            amount=amount,
            submitted_by=submitted_by,
            submitted_at=_now(),
        )
        self.session.add(offer)
        await self.session.flush()
        return offer

    async def update_thread(
        self, thread: BargainingThread, **fields
    ) -> None:
        for key, value in fields.items():
            setattr(thread, key, value)
        await self.session.flush()

    async def update_offer_outcome(
        self, offer: BargainingOffer, outcome: str
    ) -> None:
        offer.outcome = outcome
        offer.outcome_at = _now()
        await self.session.flush()

    async def get_offer(self, offer_id: uuid.UUID) -> BargainingOffer | None:
        return await self.session.get(BargainingOffer, offer_id)

    # ── Payment ───────────────────────────────────────────────────────────────

    async def get_payment_record(self, order_id: uuid.UUID) -> PaymentRecord | None:
        q = select(PaymentRecord).where(PaymentRecord.order_id == order_id)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create_payment_record(
        self,
        order_id: uuid.UUID,
        amount,
        payment_method: str,
        reference_number: str | None,
        notes: str | None,
    ) -> PaymentRecord:
        record = PaymentRecord(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def confirm_payment(
        self, payment_record: PaymentRecord, confirmed_by: uuid.UUID
    ) -> None:
        payment_record.confirmed_by = confirmed_by
        payment_record.confirmed_at = _now()
        await self.session.flush()

    # ── Vouchers ──────────────────────────────────────────────────────────────

    async def get_voucher(self, order_id: uuid.UUID) -> Voucher | None:
        q = select(Voucher).where(Voucher.order_id == order_id)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create_voucher(
        self,
        order_id: uuid.UUID,
        voucher_code: str,
        issued_by: uuid.UUID,
        notes: str | None,
    ) -> Voucher:
        voucher = Voucher(
            order_id=order_id,
            voucher_code=voucher_code,
            issued_by=issued_by,
            issued_at=_now(),
            notes=notes,
        )
        self.session.add(voucher)
        await self.session.flush()
        return voucher

    # ── Milestones ────────────────────────────────────────────────────────────

    async def list_milestones(self, order_id: uuid.UUID) -> list[FulfillmentMilestone]:
        q = select(FulfillmentMilestone).where(
            FulfillmentMilestone.order_id == order_id
        )
        return list((await self.session.execute(q)).scalars().all())

    async def add_milestone(
        self,
        order_id: uuid.UUID,
        milestone_type: str,
        description: str | None,
        recorded_by: uuid.UUID,
        occurred_at: datetime,
    ) -> FulfillmentMilestone:
        milestone = FulfillmentMilestone(
            order_id=order_id,
            milestone_type=milestone_type,
            description=description,
            recorded_by=recorded_by,
            occurred_at=occurred_at,
        )
        self.session.add(milestone)
        await self.session.flush()
        return milestone

    # ── Refunds ───────────────────────────────────────────────────────────────

    async def get_refund_record(self, order_id: uuid.UUID) -> RefundRecord | None:
        q = select(RefundRecord).where(RefundRecord.order_id == order_id)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create_refund_record(
        self,
        order_id: uuid.UUID,
        amount,
        initiated_by: uuid.UUID,
        reason: str,
    ) -> RefundRecord:
        record = RefundRecord(
            order_id=order_id,
            amount=amount,
            initiated_by=initiated_by,
            initiated_at=_now(),
            reason=reason,
            rollback_applied=False,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def process_refund(
        self, refund_record: RefundRecord, processed_by: uuid.UUID
    ) -> None:
        refund_record.processed_by = processed_by
        refund_record.processed_at = _now()
        await self.session.flush()

    async def create_rollback_event(
        self,
        refund_id: uuid.UUID,
        order_id: uuid.UUID,
        item_id: uuid.UUID,
        slots_restored: int,
        rollback_reason: str,
        rolled_back_at: datetime,
    ) -> RollbackEvent:
        evt = RollbackEvent(
            refund_id=refund_id,
            order_id=order_id,
            item_id=item_id,
            slots_restored=slots_restored,
            rollback_reason=rollback_reason,
            rolled_back_at=rolled_back_at,
        )
        self.session.add(evt)
        await self.session.flush()
        return evt

    # ── After-sales ───────────────────────────────────────────────────────────

    async def list_after_sales(self, order_id: uuid.UUID) -> list[AfterSalesRequest]:
        q = select(AfterSalesRequest).where(AfterSalesRequest.order_id == order_id)
        return list((await self.session.execute(q)).scalars().all())

    async def get_after_sales(self, request_id: uuid.UUID) -> AfterSalesRequest | None:
        return await self.session.get(AfterSalesRequest, request_id)

    async def create_after_sales(
        self,
        order_id: uuid.UUID,
        requested_by: uuid.UUID,
        request_type: str,
        description: str,
        window_expires_at: datetime,
    ) -> AfterSalesRequest:
        req = AfterSalesRequest(
            order_id=order_id,
            requested_by=requested_by,
            request_type=request_type,
            description=description,
            status="open",
            window_expires_at=window_expires_at,
        )
        self.session.add(req)
        await self.session.flush()
        return req

    async def resolve_after_sales(
        self,
        request: AfterSalesRequest,
        resolved_by: uuid.UUID,
        resolution_notes: str,
    ) -> None:
        request.resolved_by = resolved_by
        request.resolved_at = _now()
        request.resolution_notes = resolution_notes
        request.status = "resolved"
        await self.session.flush()

    # ── Worker queries ────────────────────────────────────────────────────────

    async def pending_payment_overdue(self, now: datetime) -> list[Order]:
        q = (
            select(Order)
            .options(selectinload(Order.item).selectinload(ServiceItem.inventory))
            .where(
                Order.status == "pending_payment",
                Order.auto_cancel_at <= now,
            )
        )
        return list((await self.session.execute(q)).scalars().all())

    async def open_bargaining_threads_expired(
        self, now: datetime
    ) -> list[BargainingThread]:
        q = (
            select(BargainingThread)
            .options(
                selectinload(BargainingThread.offers),
            )
            .where(
                BargainingThread.status == "open",
                BargainingThread.window_expires_at <= now,
            )
        )
        return list((await self.session.execute(q)).scalars().all())
