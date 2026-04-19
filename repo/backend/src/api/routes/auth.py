"""
Authentication & device management routes.

All routes return the shared SuccessResponse envelope from schemas.common.
Error envelopes are emitted by the handlers registered in api/errors.py.
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...domain.enums import UserRole
from ...persistence.database import get_db
from ...persistence.models.auth import User
from ...persistence.repositories.auth_repo import AuthRepository, now_utc
from ...schemas.auth import (
    DeviceActivateRequest,
    DeviceChallengeRequest,
    DeviceChallengeResponse,
    DeviceRead,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    DeviceRotateRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    PasswordChangeRequest,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
    UserRead,
)
from ...schemas.common import SuccessResponse, make_success
from ...security import device_keys, nonce as nonce_mod
from ...security.errors import SignatureInvalidError
from ...services.auth_service import AuthService
from ..dependencies import (
    CurrentUser,
    SignedRequestUser,
    require_signed_request,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        role=UserRole(user.role),
        full_name=user.full_name,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    settings = get_settings()
    now = now_utc()
    nonce_mod.assert_fresh_timestamp(
        payload.timestamp, now, settings.clock_skew_tolerance_seconds
    )
    expiry = nonce_mod.compute_nonce_expiry(now, settings.nonce_window_seconds)
    await nonce_mod.record_nonce(
        session, nonce_value=payload.nonce, expires_at=expiry, now=now
    )

    svc = AuthService(session)
    result = await svc.login(
        username=payload.username,
        password=payload.password,
        device_fingerprint=payload.device_fingerprint,
        ip_address=_client_ip(request),
        trace_id=getattr(request.state, "trace_id", None),
    )
    data = TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        user_id=result.user.id,
        role=UserRole(result.user.role),
        cohort_config=None,
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.post("/refresh", response_model=SuccessResponse[RefreshResponse])
async def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    settings = get_settings()
    now = now_utc()
    nonce_mod.assert_fresh_timestamp(
        payload.timestamp, now, settings.clock_skew_tolerance_seconds
    )
    expiry = nonce_mod.compute_nonce_expiry(now, settings.nonce_window_seconds)
    await nonce_mod.record_nonce(
        session, nonce_value=payload.nonce, expires_at=expiry, now=now
    )
    svc = AuthService(session)
    result = await svc.refresh(
        refresh_token=payload.refresh_token,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    data = RefreshResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: LogoutRequest,
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = AuthService(session)
    await svc.logout(
        refresh_token=payload.refresh_token,
        actor=user,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    return make_success(
        {"logged_out": True}, trace_id=getattr(request.state, "trace_id", None)
    )


@router.get("/me", response_model=SuccessResponse[MeResponse])
async def me(
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    candidate_id: uuid.UUID | None = None
    if user.role == UserRole.candidate:
        from ...persistence.repositories.candidate_repo import CandidateRepository

        repo = CandidateRepository(session)
        profile = await repo.get_by_user_id(user.id)
        if profile is not None:
            candidate_id = profile.id
    data = MeResponse(
        user=_user_read(user),
        cohort_config=None,
        device_id=None,
        candidate_id=candidate_id,
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.post("/password/change", response_model=SuccessResponse[dict])
async def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    user: SignedRequestUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    svc = AuthService(session)
    await svc.change_password(
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    return make_success(
        {"password_changed": True},
        trace_id=getattr(request.state, "trace_id", None),
    )


# ── Device enrollment ─────────────────────────────────────────────────────
#
# Enrollment challenges are persisted in the `device_enrollment_challenges`
# table so that outstanding bootstraps survive multi-worker deployments and
# process restarts. Consumption is single-use: the row is deleted atomically
# in the same transaction that verifies the enrollment signature.


@router.post(
    "/device/challenge",
    response_model=SuccessResponse[DeviceChallengeResponse],
)
async def device_challenge(
    payload: DeviceChallengeRequest,
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    settings = get_settings()
    ch = device_keys.generate_enrollment_challenge()
    now = now_utc()
    expires = now + timedelta(seconds=settings.nonce_window_seconds)
    repo = AuthRepository(session)
    await repo.create_enrollment_challenge(
        challenge_id=ch.challenge_id,
        nonce=ch.nonce,
        device_fingerprint=payload.device_fingerprint,
        user_id=user.id,
        expires_at=expires,
        created_at=now,
    )
    return make_success(
        DeviceChallengeResponse(
            challenge_id=ch.challenge_id,
            nonce=ch.nonce,
            expires_at=expires,
        ),
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.post(
    "/device/activate",
    response_model=SuccessResponse[DeviceRegisterResponse],
)
async def device_activate(
    payload: DeviceActivateRequest,
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    repo = AuthRepository(session)
    now = now_utc()
    challenge = await repo.consume_enrollment_challenge(
        challenge_id=payload.challenge_id, user_id=user.id, now=now
    )
    if challenge is None:
        raise SignatureInvalidError("Enrollment challenge not found or expired.")
    if challenge.device_fingerprint != payload.device_fingerprint:
        raise SignatureInvalidError("Enrollment challenge mismatch.")
    ok = device_keys.verify_enrollment_signature(
        challenge_nonce=challenge.nonce,
        signature_b64=payload.signature,
        public_key_pem=payload.public_key_pem,
    )
    if not ok:
        raise SignatureInvalidError("Enrollment signature is invalid.")
    svc = AuthService(session)
    device = await svc.register_device(
        user=user,
        device_fingerprint=payload.device_fingerprint,
        public_key_pem=payload.public_key_pem,
        label=payload.label,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    data = DeviceRegisterResponse(
        device_id=device.id,
        device_fingerprint=device.device_fingerprint,
        registered_at=device.created_at,
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.post(
    "/device/register",
    response_model=SuccessResponse[DeviceRegisterResponse],
)
async def device_register(
    payload: DeviceRegisterRequest,
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Direct registration (used for tests and service-managed devices)."""
    svc = AuthService(session)
    device = await svc.register_device(
        user=user,
        device_fingerprint=payload.device_fingerprint,
        public_key_pem=payload.public_key_pem,
        label=payload.label,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    data = DeviceRegisterResponse(
        device_id=device.id,
        device_fingerprint=device.device_fingerprint,
        registered_at=device.created_at,
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.post(
    "/device/{device_id}/rotate",
    response_model=SuccessResponse[DeviceRead],
    dependencies=[Depends(require_signed_request)],
)
async def device_rotate(
    payload: DeviceRotateRequest,
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    device_id: uuid.UUID = Path(..., description="Device to rotate."),
):
    svc = AuthService(session)
    device = await svc.rotate_device(
        user=user,
        device_id=device_id,
        new_public_key_pem=payload.new_public_key_pem,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    data = DeviceRead(
        device_id=device.id,
        device_fingerprint=device.device_fingerprint,
        label=device.label,
        is_active=device.is_active,
        last_used_at=device.last_used_at,
        registered_at=device.created_at,
    )
    return make_success(data, trace_id=getattr(request.state, "trace_id", None))


@router.delete(
    "/device/{device_id}",
    response_model=SuccessResponse[dict],
)
async def device_revoke(
    request: Request,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_db)],
    device_id: uuid.UUID = Path(..., description="Device to revoke."),
):
    svc = AuthService(session)
    await svc.revoke_device(
        user=user,
        device_id=device_id,
        trace_id=getattr(request.state, "trace_id", None),
        ip_address=_client_ip(request),
    )
    return make_success(
        {"revoked": True, "device_id": str(device_id)},
        trace_id=getattr(request.state, "trace_id", None),
    )
