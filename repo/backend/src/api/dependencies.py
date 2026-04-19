"""
FastAPI dependencies for the HTTP boundary.

Centralizes: DB session, current-user resolution, role gating, signed-request
verification (timestamp freshness + nonce recording + ECDSA signature check),
and idempotency-key extraction.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..domain.enums import UserRole
from ..persistence.database import get_db
from ..persistence.models.auth import User
from ..persistence.repositories.auth_repo import AuthRepository, now_utc
from ..security import jwt as jwt_mod
from ..security import nonce as nonce_mod
from ..security import signing
from ..security.errors import (
    AuthError,
    DeviceNotFoundError,
    ForbiddenError,
    SignatureInvalidError,
)
from ..security.rbac import Actor, coerce_role

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: DbSession,
) -> User:
    if not token:
        raise AuthError("Authentication required.")
    claims = jwt_mod.decode_access_token(token)
    try:
        user_id = uuid.UUID(claims.get("sub", ""))
    except ValueError as exc:
        raise AuthError("Access token subject is invalid.") from exc
    repo = AuthRepository(session)
    user = await repo.get_user_by_id(user_id)
    if user is None or not user.is_active or user.is_locked:
        raise AuthError("User is no longer active.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole | str):
    """Dependency factory enforcing route-level role gating."""
    wanted = [coerce_role(r) for r in roles]

    async def _dep(user: CurrentUser) -> User:
        if UserRole(user.role) not in wanted:
            raise ForbiddenError("Role is not permitted for this route.")
        return user

    return _dep


def build_actor(user: User) -> Actor:
    return Actor(
        user_id=str(user.id),
        role=UserRole(user.role),
        username=user.username,
    )


async def get_current_actor(user: CurrentUser) -> Actor:
    return build_actor(user)


CurrentActor = Annotated[Actor, Depends(get_current_actor)]


async def require_signed_request(
    request: Request,
    session: DbSession,
    user: CurrentUser,
    x_timestamp: Annotated[str | None, Header(alias="X-Timestamp")] = None,
    x_nonce: Annotated[str | None, Header(alias="X-Nonce")] = None,
    x_device_id: Annotated[str | None, Header(alias="X-Device-ID")] = None,
    x_request_signature: Annotated[
        str | None, Header(alias="X-Request-Signature")
    ] = None,
) -> User:
    """
    Verify a signed request.

    Sequence:
        1. Header presence check → SignatureInvalidError.
        2. Timestamp freshness check (±clock_skew_tolerance_seconds).
        3. Record nonce (UNIQUE → NonceReplayError).
        4. Look up device by ID; verify ECDSA signature over canonical form.
    """
    if not (x_timestamp and x_nonce and x_device_id and x_request_signature):
        raise SignatureInvalidError("Missing signing headers.")

    settings = get_settings()
    now = now_utc()
    client_ts = nonce_mod.assert_fresh_timestamp(
        x_timestamp, now, settings.clock_skew_tolerance_seconds
    )

    try:
        device_id = uuid.UUID(x_device_id)
    except ValueError as exc:
        raise SignatureInvalidError("Invalid device id.") from exc

    expiry = nonce_mod.compute_nonce_expiry(now, settings.nonce_window_seconds)
    await nonce_mod.record_nonce(
        session,
        nonce_value=x_nonce,
        expires_at=expiry,
        user_id=user.id,
        now=now,
    )

    body = await request.body()
    method = request.method.upper()
    path = request.url.path
    canonical = signing.build_canonical_string(
        method=method,
        path=path,
        timestamp=x_timestamp,
        nonce=x_nonce,
        device_id=x_device_id,
        body_bytes=body,
    )

    repo = AuthRepository(session)
    device = await repo.get_device_by_id(device_id)
    if device is None or not device.is_active:
        raise DeviceNotFoundError("Device not registered or inactive.")
    if device.user_id != user.id:
        raise ForbiddenError("Device does not belong to the authenticated user.")

    if not signing.verify_signature(
        device.public_key_pem, canonical, x_request_signature
    ):
        raise SignatureInvalidError("Request signature is invalid.")
    await repo.touch_device_used(device, now=now)
    _ = client_ts  # suppress unused
    return user


SignedRequestUser = Annotated[User, Depends(require_signed_request)]


async def idempotency_key_dep(
    idempotency_key: Annotated[
        str | None, Header(alias="Idempotency-Key")
    ] = None,
) -> str | None:
    if idempotency_key is None:
        return None
    if len(idempotency_key) < 8 or len(idempotency_key) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must be 8..128 characters.",
        )
    return idempotency_key


IdempotencyKeyHeader = Annotated[str | None, Depends(idempotency_key_dep)]
