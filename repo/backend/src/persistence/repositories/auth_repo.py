"""
Repository for auth-related tables: users, devices, refresh-token families,
refresh tokens, login throttles, IdP clients.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auth import (
    DeviceEnrollmentChallenge,
    DeviceRegistration,
    IdpClient,
    LoginThrottle,
    Nonce,
    RefreshToken,
    RefreshTokenFamily,
    User,
)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Users ────────────────────────────────────────────────────────────
    async def get_user_by_username(self, username: str) -> User | None:
        q = select(User).where(User.username == username)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        role: str,
        full_name: str,
    ) -> User:
        u = User(
            username=username,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
            is_active=True,
            is_locked=False,
        )
        self.session.add(u)
        await self.session.flush()
        return u

    async def set_user_password_hash(self, user: User, new_hash: str) -> None:
        user.password_hash = new_hash
        await self.session.flush()

    async def touch_last_login(self, user: User, now: datetime) -> None:
        user.last_login_at = now
        await self.session.flush()

    # ── Devices ──────────────────────────────────────────────────────────
    async def get_device(
        self, *, user_id: uuid.UUID, device_id: uuid.UUID
    ) -> DeviceRegistration | None:
        q = select(DeviceRegistration).where(
            DeviceRegistration.id == device_id,
            DeviceRegistration.user_id == user_id,
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def get_device_by_id(self, device_id: uuid.UUID) -> DeviceRegistration | None:
        return await self.session.get(DeviceRegistration, device_id)

    async def insert_device(
        self,
        *,
        user_id: uuid.UUID,
        device_fingerprint: str,
        public_key_pem: str,
        label: str | None,
    ) -> DeviceRegistration:
        d = DeviceRegistration(
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            public_key_pem=public_key_pem,
            label=label,
            is_active=True,
        )
        self.session.add(d)
        await self.session.flush()
        return d

    async def rotate_device_key(
        self, device: DeviceRegistration, *, new_public_key_pem: str
    ) -> None:
        device.public_key_pem = new_public_key_pem
        await self.session.flush()

    async def revoke_device(
        self, device: DeviceRegistration, *, now: datetime
    ) -> None:
        device.is_active = False
        device.revoked_at = now
        await self.session.flush()

    async def touch_device_used(
        self, device: DeviceRegistration, *, now: datetime
    ) -> None:
        device.last_used_at = now
        await self.session.flush()

    # ── Refresh token families ──────────────────────────────────────────
    async def create_family(
        self, *, user_id: uuid.UUID, device_id: uuid.UUID | None
    ) -> RefreshTokenFamily:
        fam = RefreshTokenFamily(user_id=user_id, device_id=device_id, is_invalidated=False)
        self.session.add(fam)
        await self.session.flush()
        return fam

    async def invalidate_family(
        self, family: RefreshTokenFamily, *, reason: str, now: datetime
    ) -> None:
        family.is_invalidated = True
        family.invalidated_at = now
        family.invalidation_reason = reason
        await self.session.flush()

    async def get_family(self, family_id: uuid.UUID) -> RefreshTokenFamily | None:
        return await self.session.get(RefreshTokenFamily, family_id)

    # ── Refresh tokens ──────────────────────────────────────────────────
    async def insert_refresh_token(
        self,
        *,
        family_id: uuid.UUID,
        token_hash: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> RefreshToken:
        t = RefreshToken(
            family_id=family_id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            is_consumed=False,
        )
        self.session.add(t)
        await self.session.flush()
        return t

    async def get_refresh_token_by_hash(
        self, token_hash: str
    ) -> RefreshToken | None:
        q = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def mark_refresh_token_consumed(
        self, token: RefreshToken, *, now: datetime
    ) -> None:
        token.is_consumed = True
        token.consumed_at = now
        await self.session.flush()

    # ── Throttling ──────────────────────────────────────────────────────
    async def get_throttle(self, username: str) -> LoginThrottle | None:
        q = (
            select(LoginThrottle)
            .where(LoginThrottle.username == username)
            .order_by(LoginThrottle.window_start.desc())
            .limit(1)
        )
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def create_throttle(
        self, *, username: str, now: datetime
    ) -> LoginThrottle:
        t = LoginThrottle(
            username=username,
            window_start=now,
            attempt_count=1,
            last_attempt_at=now,
        )
        self.session.add(t)
        await self.session.flush()
        return t

    async def increment_throttle(
        self, throttle: LoginThrottle, *, now: datetime
    ) -> None:
        throttle.attempt_count += 1
        throttle.last_attempt_at = now
        await self.session.flush()

    async def lock_throttle(
        self, throttle: LoginThrottle, *, until: datetime
    ) -> None:
        throttle.locked_until = until
        await self.session.flush()

    async def reset_throttle(self, throttle: LoginThrottle, *, now: datetime) -> None:
        throttle.attempt_count = 0
        throttle.window_start = now
        throttle.last_attempt_at = now
        throttle.locked_until = None
        await self.session.flush()

    # ── IdP clients ─────────────────────────────────────────────────────
    async def get_idp_client(self, client_id: str) -> IdpClient | None:
        q = select(IdpClient).where(IdpClient.client_id == client_id)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    # ── Nonces ──────────────────────────────────────────────────────────
    async def purge_expired_nonces(self, *, now: datetime) -> int:
        """Best-effort cleanup helper. Returns number of rows deleted."""
        q = select(Nonce).where(Nonce.expires_at < now)
        res = await self.session.execute(q)
        rows: Sequence[Nonce] = res.scalars().all()
        for row in rows:
            await self.session.delete(row)
        await self.session.flush()
        return len(rows)

    # ── Device enrollment challenges ────────────────────────────────────
    async def create_enrollment_challenge(
        self,
        *,
        challenge_id: str,
        nonce: str,
        device_fingerprint: str,
        user_id: uuid.UUID,
        expires_at: datetime,
        created_at: datetime,
    ) -> DeviceEnrollmentChallenge:
        row = DeviceEnrollmentChallenge(
            challenge_id=challenge_id,
            nonce=nonce,
            device_fingerprint=device_fingerprint,
            user_id=user_id,
            expires_at=expires_at,
            created_at=created_at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def consume_enrollment_challenge(
        self, *, challenge_id: str, user_id: uuid.UUID, now: datetime
    ) -> DeviceEnrollmentChallenge | None:
        """
        Atomically look up and delete the challenge row.

        Returns the row if it existed, matched the user, and was unexpired.
        Returns None if the row is absent, expired, or belongs to a different user.
        The delete happens inside the caller's transaction, making consumption
        single-use by construction.
        """
        row = await self.session.get(DeviceEnrollmentChallenge, challenge_id)
        if row is None:
            return None
        if row.user_id != user_id:
            return None
        if _as_utc(row.expires_at) <= _as_utc(now):
            await self.session.delete(row)
            await self.session.flush()
            return None
        await self.session.delete(row)
        await self.session.flush()
        return row

    async def purge_expired_enrollment_challenges(self, *, now: datetime) -> int:
        q = select(DeviceEnrollmentChallenge).where(
            DeviceEnrollmentChallenge.expires_at < now
        )
        res = await self.session.execute(q)
        rows: Sequence[DeviceEnrollmentChallenge] = res.scalars().all()
        for row in rows:
            await self.session.delete(row)
        await self.session.flush()
        return len(rows)


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)
