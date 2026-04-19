import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey,
    Index, Integer, Numeric, SmallInteger, String,
    Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ServiceItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "service_items"
    __table_args__ = (
        UniqueConstraint("item_code", name="uq_service_item_code"),
    )

    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    pricing_mode: Mapped[str] = mapped_column(
        String(20), default="fixed", nullable=False
    )
    fixed_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    is_capacity_limited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bargaining_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inventory: Mapped["ServiceItemInventory | None"] = relationship(
        back_populates="item", uselist=False
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="item")


class ServiceItemInventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "service_item_inventory"
    __table_args__ = (
        UniqueConstraint("item_id", name="uq_inventory_item"),
        CheckConstraint("reserved_count <= total_slots", name="ck_inventory_reserved_le_total"),
        CheckConstraint("total_slots >= 0", name="ck_inventory_total_nonneg"),
        CheckConstraint("reserved_count >= 0", name="ck_inventory_reserved_nonneg"),
    )

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_items.id", ondelete="CASCADE"), nullable=False
    )
    total_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    item: Mapped["ServiceItem"] = relationship(back_populates="inventory")


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_candidate_id", "candidate_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_items.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending_payment", nullable=False
    )
    pricing_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    agreed_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    auto_cancel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    idempotency_key: Mapped[str | None] = mapped_column(String(64))

    item: Mapped["ServiceItem"] = relationship(back_populates="orders")
    events: Mapped[list["OrderEvent"]] = relationship(
        back_populates="order", order_by="OrderEvent.sequence_number"
    )
    bargaining_thread: Mapped["BargainingThread | None"] = relationship(
        back_populates="order", uselist=False
    )
    payment_record: Mapped["PaymentRecord | None"] = relationship(
        back_populates="order", uselist=False
    )
    voucher: Mapped["Voucher | None"] = relationship(back_populates="order", uselist=False)
    milestones: Mapped[list["FulfillmentMilestone"]] = relationship(back_populates="order")
    refund_records: Mapped[list["RefundRecord"]] = relationship(back_populates="order")
    after_sales_requests: Mapped[list["AfterSalesRequest"]] = relationship(back_populates="order")


class OrderEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "order_events"
    __table_args__ = (
        UniqueConstraint("order_id", "sequence_number", name="uq_order_event_seq"),
        Index("ix_order_events_order_id", "order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(30))
    new_state: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_role: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="events")


class BargainingThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bargaining_threads"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_bargaining_thread_order"),
        CheckConstraint("counter_count <= 1", name="ck_thread_counter_max_one"),
        CheckConstraint("counter_count >= 0", name="ck_thread_counter_nonneg"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    window_starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    counter_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    counter_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    counter_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    counter_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_offer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped["Order"] = relationship(back_populates="bargaining_thread")
    offers: Mapped[list["BargainingOffer"]] = relationship(
        back_populates="thread", order_by="BargainingOffer.offer_number"
    )


class BargainingOffer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "bargaining_offers"
    __table_args__ = (
        UniqueConstraint("thread_id", "offer_number", name="uq_bargaining_offer_number"),
        CheckConstraint("offer_number IN (1, 2, 3)", name="ck_offer_number_max_three"),
        CheckConstraint("amount > 0", name="ck_offer_amount_positive"),
        Index("ix_bargaining_offers_thread_id", "thread_id"),
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bargaining_threads.id", ondelete="CASCADE"), nullable=False
    )
    offer_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(30))
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    thread: Mapped["BargainingThread"] = relationship(back_populates="offers")


class PaymentRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_records"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payment_order"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(200))
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="payment_record")


class Voucher(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_voucher_order"),
        UniqueConstraint("voucher_code", name="uq_voucher_code"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    voucher_code: Mapped[str] = mapped_column(String(100), nullable=False)
    issued_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="voucher")


class FulfillmentMilestone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fulfillment_milestones"
    __table_args__ = (
        Index("ix_milestones_order_id", "order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    milestone_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="milestones")


class AfterSalesRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "after_sales_requests"
    __table_args__ = (
        Index("ix_after_sales_order_id", "order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    request_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    window_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship(back_populates="after_sales_requests")


class RefundRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refund_records"
    __table_args__ = (
        Index("ix_refund_records_order_id", "order_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    initiated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    rollback_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="refund_records")
    rollback_event: Mapped["RollbackEvent | None"] = relationship(
        back_populates="refund", uselist=False
    )


class RollbackEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rollback_events"
    __table_args__ = (
        UniqueConstraint("refund_id", name="uq_rollback_refund"),
    )

    refund_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refund_records.id", ondelete="RESTRICT"), nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    slots_restored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rollback_reason: Mapped[str] = mapped_column(String(200), nullable=False)
    rolled_back_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    refund: Mapped["RefundRecord"] = relationship(back_populates="rollback_event")
