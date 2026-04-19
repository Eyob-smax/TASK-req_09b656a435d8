import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AttendanceAnomaly(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attendance_anomalies"
    __table_args__ = (
        Index("ix_anomalies_candidate_id", "candidate_id"),
        Index("ix_anomalies_flagged_by", "flagged_by"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    anomaly_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    session_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_identifier: Mapped[str | None] = mapped_column(String(200))
    flagged_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    flagged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    exceptions: Mapped[list["AttendanceException"]] = relationship(back_populates="anomaly")


class AttendanceException(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attendance_exceptions"
    __table_args__ = (
        Index("ix_exceptions_candidate_id", "candidate_id"),
        Index("ix_exceptions_status", "status"),
    )

    anomaly_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_anomalies.id", ondelete="SET NULL")
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending_proof", nullable=False
    )
    current_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    candidate_statement: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    anomaly: Mapped["AttendanceAnomaly | None"] = relationship(back_populates="exceptions")
    proofs: Mapped[list["ExceptionProof"]] = relationship(back_populates="exception")
    review_steps: Mapped[list["ExceptionReviewStep"]] = relationship(
        back_populates="exception", order_by="ExceptionReviewStep.step_order"
    )


class ExceptionProof(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "exception_proofs"
    __table_args__ = (
        Index("ix_exception_proofs_exception_id", "exception_id"),
    )

    exception_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_exceptions.id", ondelete="CASCADE"), nullable=False
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    exception: Mapped["AttendanceException"] = relationship(back_populates="proofs")


class ExceptionReviewStep(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "exception_review_steps"
    __table_args__ = (
        UniqueConstraint("exception_id", "step_order", name="uq_review_step_order"),
        Index("ix_review_steps_exception_id", "exception_id"),
    )

    exception_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_exceptions.id", ondelete="CASCADE"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reviewer_role: Mapped[str] = mapped_column(String(20), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    exception: Mapped["AttendanceException"] = relationship(back_populates="review_steps")
    approval: Mapped["ExceptionApproval | None"] = relationship(
        back_populates="step", uselist=False
    )


class ExceptionApproval(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "exception_approvals"
    __table_args__ = (
        UniqueConstraint("step_id", name="uq_approval_step"),
    )

    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exception_review_steps.id", ondelete="RESTRICT"), nullable=False
    )
    exception_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_exceptions.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    signature_hash: Mapped[str | None] = mapped_column(String(128))

    step: Mapped["ExceptionReviewStep"] = relationship(back_populates="approval")
