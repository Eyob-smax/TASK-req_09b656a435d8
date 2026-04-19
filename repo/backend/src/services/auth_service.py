"""
Authentication orchestration.

Handles login, refresh, logout, password change, and device enrollment
using the AuthRepository and security primitives. Emits audit events and
metrics, enforces login throttling, rotates refresh tokens, and detects
refresh-token reuse (invalidating the entire family).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..domain.enums import AuditEventType, UserRole
from ..persistence.models.auth import (
    DeviceRegistration,
    RefreshToken,
    RefreshTokenFamily,
    User,
)
from ..persistence.repositories.auth_repo import AuthRepository, now_utc
from ..security import audit as audit_mod
from ..security import device_keys, jwt as jwt_mod, passwords, refresh_tokens, throttling
from ..security.errors import (
    AuthError,
    DeviceNotFoundError,
    ForbiddenError,
    SignatureInvalidError,
    ThrottledError,
)
from ..telemetry import metrics


@dataclass
class LoginResult:
    user: User
    access_token: str
    refresh_token: str
    refresh_token_hash: str
    family: RefreshTokenFamily
    device: DeviceRegistration | None
    expires_in: int


@dataclass
class RefreshResult:
    user: User
    access_token: str
    refresh_token: str
    refresh_token_hash: str
    family: RefreshTokenFamily
    expires_in: int


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuthRepository(session)
        self.settings = get_settings()

    # ── Login ────────────────────────────────────────────────────────────
    async def login(
        self,
        *,
        username: str,
        password: str,
        device_fingerprint: str | None,
        ip_address: str | None = None,
        trace_id: str | None = None,
    ) -> LoginResult:
        now = now_utc()
        throttle = await self.repo.get_throttle(username)
        if throttle is not None:
            if throttling.is_locked(throttle.locked_until, now):
                metrics.login_attempts_total.inc(outcome="throttled")
                await audit_mod.record_audit(
                    self.session,
                    event_type=AuditEventType.login_failure.value,
                    actor_id=None,
                    actor_role=None,
                    outcome="throttled",
                    detail={"username": username, "reason": "locked"},
                    trace_id=trace_id,
                    ip_address=ip_address,
                )
                raise ThrottledError("Too many login attempts; try again later.")

        user = await self.repo.get_user_by_username(username)
        invalid_credentials = False
        if user is None or not user.is_active or user.is_locked:
            invalid_credentials = True
        else:
            try:
                ok = passwords.verify_password(password, user.password_hash)
            except Exception:
                ok = False
            if not ok:
                invalid_credentials = True

        if invalid_credentials:
            await self._register_failed_attempt(username, now, trace_id, ip_address)
            metrics.login_attempts_total.inc(outcome="failure")
            raise AuthError("Invalid username or password.")

        if throttle is not None:
            await self.repo.reset_throttle(throttle, now=now)

        device: DeviceRegistration | None = None
        if device_fingerprint:
            device = await self._find_active_device(user.id, device_fingerprint)

        family = await self.repo.create_family(
            user_id=user.id, device_id=device.id if device else None
        )
        opaque = refresh_tokens.generate_opaque_token()
        token_hash = refresh_tokens.hash_refresh_token(opaque)
        refresh_expiry = now + timedelta(days=self.settings.refresh_token_expire_days)
        await self.repo.insert_refresh_token(
            family_id=family.id,
            token_hash=token_hash,
            issued_at=now,
            expires_at=refresh_expiry,
        )
        await self.repo.touch_last_login(user, now)

        access_ttl = self.settings.access_token_expire_minutes * 60
        access_token = jwt_mod.create_access_token(
            user_id=str(user.id),
            role=user.role,
            extra_claims={
                "family_id": str(family.id),
                "device_id": str(device.id) if device else None,
            },
            ttl_seconds=access_ttl,
        )

        metrics.login_attempts_total.inc(outcome="success")
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.login_success.value,
            actor_id=user.id,
            actor_role=user.role,
            resource_type="user",
            resource_id=str(user.id),
            outcome="success",
            detail={
                "device_id": str(device.id) if device else None,
                "family_id": str(family.id),
            },
            trace_id=trace_id,
            ip_address=ip_address,
        )

        return LoginResult(
            user=user,
            access_token=access_token,
            refresh_token=opaque,
            refresh_token_hash=token_hash,
            family=family,
            device=device,
            expires_in=access_ttl,
        )

    async def _register_failed_attempt(
        self,
        username: str,
        now: datetime,
        trace_id: str | None,
        ip_address: str | None,
    ) -> None:
        throttle = await self.repo.get_throttle(username)
        if throttle is None:
            await self.repo.create_throttle(username=username, now=now)
            throttle = await self.repo.get_throttle(username)
        else:
            if throttling.reset_needed(
                throttle.window_start, now, self.settings.login_throttle_window_minutes
            ):
                await self.repo.reset_throttle(throttle, now=now)
                throttle.attempt_count = 1
            else:
                await self.repo.increment_throttle(throttle, now=now)

        if throttle is not None and throttling.should_throttle(
            throttle.attempt_count,
            throttle.window_start,
            now,
            self.settings.login_throttle_max_attempts,
            self.settings.login_throttle_window_minutes,
        ):
            until = throttling.compute_lockout_until(
                now, self.settings.login_lockout_minutes
            )
            await self.repo.lock_throttle(throttle, until=until)

        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.login_failure.value,
            actor_id=None,
            actor_role=None,
            outcome="failure",
            detail={"username": username},
            trace_id=trace_id,
            ip_address=ip_address,
        )
        await self.session.commit()

    async def _find_active_device(
        self, user_id: uuid.UUID, fingerprint: str
    ) -> DeviceRegistration | None:
        from sqlalchemy import select

        q = select(DeviceRegistration).where(
            DeviceRegistration.user_id == user_id,
            DeviceRegistration.device_fingerprint == fingerprint,
            DeviceRegistration.is_active.is_(True),
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    # ── Refresh rotation ─────────────────────────────────────────────────
    async def refresh(
        self,
        *,
        refresh_token: str,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshResult:
        now = now_utc()
        token_hash = refresh_tokens.hash_refresh_token(refresh_token)
        stored = await self.repo.get_refresh_token_by_hash(token_hash)
        if stored is None:
            raise AuthError("Refresh token is invalid.")
        family = await self.repo.get_family(stored.family_id)
        if family is None or family.is_invalidated:
            raise AuthError("Refresh token family has been invalidated.")

        if stored.is_consumed:
            await self.repo.invalidate_family(
                family, reason="reuse_detected", now=now
            )
            await audit_mod.record_audit(
                self.session,
                event_type=AuditEventType.login_failure.value,
                actor_id=family.user_id,
                actor_role=None,
                resource_type="refresh_token_family",
                resource_id=str(family.id),
                outcome="reuse_detected",
                detail={"reason": "refresh_token_reuse"},
                trace_id=trace_id,
                ip_address=ip_address,
            )
            await self.session.commit()
            raise AuthError("Refresh token reuse detected; session revoked.")

        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise AuthError("Refresh token is expired.")

        user = await self.repo.get_user_by_id(family.user_id)
        if user is None or not user.is_active or user.is_locked:
            raise AuthError("User is not permitted to refresh.")

        await self.repo.mark_refresh_token_consumed(stored, now=now)

        new_opaque = refresh_tokens.generate_opaque_token()
        new_hash = refresh_tokens.hash_refresh_token(new_opaque)
        new_expiry = now + timedelta(days=self.settings.refresh_token_expire_days)
        await self.repo.insert_refresh_token(
            family_id=family.id,
            token_hash=new_hash,
            issued_at=now,
            expires_at=new_expiry,
        )

        access_ttl = self.settings.access_token_expire_minutes * 60
        access_token = jwt_mod.create_access_token(
            user_id=str(user.id),
            role=user.role,
            extra_claims={
                "family_id": str(family.id),
                "device_id": str(family.device_id) if family.device_id else None,
            },
            ttl_seconds=access_ttl,
        )
        return RefreshResult(
            user=user,
            access_token=access_token,
            refresh_token=new_opaque,
            refresh_token_hash=new_hash,
            family=family,
            expires_in=access_ttl,
        )

    # ── Logout ───────────────────────────────────────────────────────────
    async def logout(
        self,
        *,
        refresh_token: str,
        actor: User,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        now = now_utc()
        token_hash = refresh_tokens.hash_refresh_token(refresh_token)
        stored = await self.repo.get_refresh_token_by_hash(token_hash)
        if stored is None:
            return
        family = await self.repo.get_family(stored.family_id)
        if family is None:
            return
        if family.user_id != actor.id:
            raise ForbiddenError("Refresh token does not belong to actor.")
        if not family.is_invalidated:
            await self.repo.invalidate_family(family, reason="logout", now=now)
        if not stored.is_consumed:
            await self.repo.mark_refresh_token_consumed(stored, now=now)
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.logout.value,
            actor_id=actor.id,
            actor_role=actor.role,
            resource_type="refresh_token_family",
            resource_id=str(family.id),
            outcome="success",
            trace_id=trace_id,
            ip_address=ip_address,
        )

    # ── Password change ──────────────────────────────────────────────────
    async def change_password(
        self,
        *,
        user: User,
        current_password: str,
        new_password: str,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        passwords.validate_password_policy(new_password)
        if not passwords.verify_password(current_password, user.password_hash):
            raise AuthError("Current password is incorrect.")
        new_hash = passwords.hash_password(new_password)
        await self.repo.set_user_password_hash(user, new_hash)
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.password_changed.value,
            actor_id=user.id,
            actor_role=user.role,
            resource_type="user",
            resource_id=str(user.id),
            outcome="success",
            trace_id=trace_id,
            ip_address=ip_address,
        )

    # ── Devices ──────────────────────────────────────────────────────────
    async def register_device(
        self,
        *,
        user: User,
        device_fingerprint: str,
        public_key_pem: str,
        label: str | None,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> DeviceRegistration:
        device_keys.import_spki_pem(public_key_pem)
        device = await self.repo.insert_device(
            user_id=user.id,
            device_fingerprint=device_fingerprint,
            public_key_pem=public_key_pem,
            label=label,
        )
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.device_registered.value,
            actor_id=user.id,
            actor_role=user.role,
            resource_type="device",
            resource_id=str(device.id),
            outcome="success",
            detail={"fingerprint": device_fingerprint, "label": label},
            trace_id=trace_id,
            ip_address=ip_address,
        )
        return device

    async def rotate_device(
        self,
        *,
        user: User,
        device_id: uuid.UUID,
        new_public_key_pem: str,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> DeviceRegistration:
        device = await self.repo.get_device(user_id=user.id, device_id=device_id)
        if device is None or not device.is_active:
            raise DeviceNotFoundError("Device not found.")
        device_keys.import_spki_pem(new_public_key_pem)
        await self.repo.rotate_device_key(device, new_public_key_pem=new_public_key_pem)
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.device_registered.value,
            actor_id=user.id,
            actor_role=user.role,
            resource_type="device",
            resource_id=str(device.id),
            outcome="rotated",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        return device

    async def revoke_device(
        self,
        *,
        user: User,
        device_id: uuid.UUID,
        trace_id: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        now = now_utc()
        device = await self.repo.get_device(user_id=user.id, device_id=device_id)
        if device is None:
            raise DeviceNotFoundError("Device not found.")
        if device.is_active:
            await self.repo.revoke_device(device, now=now)
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.device_revoked.value,
            actor_id=user.id,
            actor_role=user.role,
            resource_type="device",
            resource_id=str(device.id),
            outcome="success",
            trace_id=trace_id,
            ip_address=ip_address,
        )

    async def verify_device_signature(
        self,
        *,
        device_id: uuid.UUID,
        canonical: bytes,
        signature_b64: str,
    ) -> DeviceRegistration:
        from ..security import signing

        device = await self.repo.get_device_by_id(device_id)
        if device is None or not device.is_active:
            raise DeviceNotFoundError("Device not registered or inactive.")
        if not signing.verify_signature(device.public_key_pem, canonical, signature_b64):
            metrics.signature_failures_total.inc(reason="bad_signature")
            raise SignatureInvalidError("Request signature is invalid.")
        await self.repo.touch_device_used(device, now=now_utc())
        return device
