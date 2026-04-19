import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer,
    SmallInteger, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
    )

    username: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    device_registrations: Mapped[list["DeviceRegistration"]] = relationship(back_populates="user")
    refresh_token_families: Mapped[list["RefreshTokenFamily"]] = relationship(back_populates="user")
    login_throttles: Mapped[list["LoginThrottle"]] = relationship(back_populates="user")


class DeviceRegistration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "device_registrations"
    __table_args__ = (
        UniqueConstraint("user_id", "device_fingerprint", name="uq_device_user_fp"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    public_key_pem: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="device_registrations")


class RefreshTokenFamily(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_token_families"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("device_registrations.id", ondelete="SET NULL")
    )
    is_invalidated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidation_reason: Mapped[str | None] = mapped_column(String(100))

    user: Mapped["User"] = relationship(back_populates="refresh_token_families")
    tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="family")


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_token_hash"),
        Index("ix_refresh_tokens_family_id", "family_id"),
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refresh_token_families.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    family: Mapped["RefreshTokenFamily"] = relationship(back_populates="tokens")


class Nonce(Base):
    __tablename__ = "nonces"
    __table_args__ = (
        UniqueConstraint("nonce_value", name="uq_nonce_value"),
        Index("ix_nonces_expires_at", "expires_at"),
    )

    nonce_value: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class LoginThrottle(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "login_throttles"
    __table_args__ = (
        Index("ix_login_throttle_username_window", "username", "window_start"),
    )

    username: Mapped[str] = mapped_column(String(150), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="login_throttles", foreign_keys="[LoginThrottle.username]", primaryjoin="LoginThrottle.username == User.username", viewonly=True)


class IdpClient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "idp_clients"
    __table_args__ = (
        UniqueConstraint("client_id", name="uq_idp_client_id"),
    )

    client_id: Mapped[str] = mapped_column(String(128), nullable=False)
    client_secret_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    allowed_scopes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class DeviceEnrollmentChallenge(Base):
    """
    Short-lived enrollment challenge for device activation bootstrap.

    Persisted (not in-memory) so that multi-worker deployments and process
    restarts do not lose outstanding challenges. Consumption is single-use:
    the row is deleted atomically in the same transaction that verifies the
    signature during /auth/device/activate.
    """

    __tablename__ = "device_enrollment_challenges"
    __table_args__ = (
        UniqueConstraint("nonce", name="uq_enroll_challenge_nonce"),
        Index("ix_enroll_challenge_expires_at", "expires_at"),
    )

    challenge_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    device_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
