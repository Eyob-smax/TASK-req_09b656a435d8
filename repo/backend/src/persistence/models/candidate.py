import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, String,
    Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_candidate_profile_user"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # Encrypted sensitive fields — stored as ciphertext; DEK id tracked separately
    ssn_encrypted: Mapped[str | None] = mapped_column(Text)
    ssn_key_version: Mapped[str | None] = mapped_column(String(64))
    date_of_birth_encrypted: Mapped[str | None] = mapped_column(Text)
    dob_key_version: Mapped[str | None] = mapped_column(String(64))
    contact_phone_encrypted: Mapped[str | None] = mapped_column(Text)
    phone_key_version: Mapped[str | None] = mapped_column(String(64))
    contact_email_encrypted: Mapped[str | None] = mapped_column(Text)
    email_key_version: Mapped[str | None] = mapped_column(String(64))

    # Non-sensitive profile fields
    preferred_name: Mapped[str | None] = mapped_column(String(255))
    application_year: Mapped[int | None] = mapped_column()
    application_status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    program_code: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    exam_scores: Mapped[list["ExamScore"]] = relationship(lazy="selectin", back_populates="candidate")
    transfer_preferences: Mapped[list["TransferPreference"]] = relationship(lazy="selectin", back_populates="candidate")
    history: Mapped[list["ProfileHistory"]] = relationship(lazy="selectin", back_populates="candidate")


class ExamScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exam_scores"
    __table_args__ = (
        UniqueConstraint("candidate_id", "subject_code", name="uq_exam_score_candidate_subject"),
        Index("ix_exam_scores_candidate_id", "candidate_id"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False
    )
    subject_code: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[str] = mapped_column(String(50), nullable=False)
    max_score: Mapped[str | None] = mapped_column(String(50))
    exam_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    candidate: Mapped["CandidateProfile"] = relationship(lazy="selectin", back_populates="exam_scores")


class TransferPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transfer_preferences"
    __table_args__ = (
        Index("ix_transfer_prefs_candidate_id", "candidate_id"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False
    )
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    program_code: Mapped[str | None] = mapped_column(String(50))
    priority_rank: Mapped[int] = mapped_column(default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    candidate: Mapped["CandidateProfile"] = relationship(lazy="selectin", back_populates="transfer_preferences")


class ProfileHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "profile_history"
    __table_args__ = (
        Index("ix_profile_history_candidate_id", "candidate_id"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value_encrypted: Mapped[str | None] = mapped_column(Text)
    new_value_encrypted: Mapped[str | None] = mapped_column(Text)
    change_reason: Mapped[str | None] = mapped_column(String(500))

    candidate: Mapped["CandidateProfile"] = relationship(lazy="selectin", back_populates="history")
