"""
High-level audit helpers.

Wraps `security.audit.record_audit` with call-site-specific semantics used
by auth / idp / signature flows. Keeps router code free of repetitive
event-type constants.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.enums import AuditEventType
from ..security import audit as audit_mod


async def audit_login_success(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    actor_role: str,
    detail: dict[str, Any] | None = None,
    trace_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    await audit_mod.record_audit(
        session,
        event_type=AuditEventType.login_success.value,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="user",
        resource_id=str(actor_id),
        outcome="success",
        detail=detail,
        trace_id=trace_id,
        ip_address=ip_address,
    )


async def audit_login_failure(
    session: AsyncSession,
    *,
    username: str,
    reason: str,
    trace_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    await audit_mod.record_audit(
        session,
        event_type=AuditEventType.login_failure.value,
        actor_id=None,
        actor_role=None,
        outcome="failure",
        detail={"username": username, "reason": reason},
        trace_id=trace_id,
        ip_address=ip_address,
    )


async def audit_password_change(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    actor_role: str,
    trace_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    await audit_mod.record_audit(
        session,
        event_type=AuditEventType.password_changed.value,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="user",
        resource_id=str(actor_id),
        outcome="success",
        trace_id=trace_id,
        ip_address=ip_address,
    )


async def audit_device_registered(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    actor_role: str,
    device_id: uuid.UUID,
    fingerprint: str,
    trace_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    await audit_mod.record_audit(
        session,
        event_type=AuditEventType.device_registered.value,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="device",
        resource_id=str(device_id),
        outcome="success",
        detail={"fingerprint": fingerprint},
        trace_id=trace_id,
        ip_address=ip_address,
    )


async def audit_device_revoked(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID,
    actor_role: str,
    device_id: uuid.UUID,
    trace_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    await audit_mod.record_audit(
        session,
        event_type=AuditEventType.device_revoked.value,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type="device",
        resource_id=str(device_id),
        outcome="success",
        trace_id=trace_id,
        ip_address=ip_address,
    )


async def audit_signature_failure(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    device_id: uuid.UUID | None,
    path: str,
    reason: str,
    trace_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    await audit_mod.record_audit(
        session,
        event_type=AuditEventType.login_failure.value,
        actor_id=actor_id,
        actor_role=None,
        resource_type="request",
        resource_id=path,
        outcome="signature_invalid",
        detail={
            "reason": reason,
            "device_id": str(device_id) if device_id else None,
        },
        trace_id=trace_id,
        ip_address=ip_address,
    )
