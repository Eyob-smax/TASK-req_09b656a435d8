"""
Immutable audit writer.

- `record_audit()` INSERTs into `audit_events`. No UPDATE or DELETE paths.
- `diff_fields()` computes a sanitized before/after diff, redacting sensitive
  keys so passwords, tokens, and raw public keys never reach the audit trail.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.enums import AuditEventType
from ..persistence.models.config_audit import AuditEvent

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "current_password",
        "new_password",
        "password_hash",
        "refresh_token",
        "access_token",
        "token",
        "client_secret",
        "client_secret_hash",
        "public_key_pem",
        "private_key_pem",
        "signature",
        "ssn",
        "date_of_birth",
        "dob",
    }
)

REDACTED = "[REDACTED]"


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: (REDACTED if k.lower() in SENSITIVE_KEYS else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def redact_sensitive(payload: dict | None) -> dict | None:
    if payload is None:
        return None
    return _redact(payload)


def diff_fields(
    before: dict | None,
    after: dict | None,
    sensitive_keys: set[str] | None = None,
) -> dict:
    before = before or {}
    after = after or {}
    sensitive = SENSITIVE_KEYS | (sensitive_keys or set())
    changed: dict[str, dict] = {}
    for key in set(before) | set(after):
        if before.get(key) == after.get(key):
            continue
        if key.lower() in sensitive:
            changed[key] = {"before": REDACTED, "after": REDACTED}
            continue
        changed[key] = {"before": before.get(key), "after": after.get(key)}
    return changed


async def record_audit(
    session: AsyncSession,
    *,
    event_type: AuditEventType | str,
    actor_id=None,
    actor_role: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: str = "success",
    detail: dict | None = None,
    trace_id: str | None = None,
    ip_address: str | None = None,
    now: datetime | None = None,
) -> AuditEvent:
    et = event_type.value if isinstance(event_type, AuditEventType) else event_type
    row = AuditEvent(
        event_type=et,
        actor_id=actor_id,
        actor_role=actor_role,
        resource_type=resource_type,
        resource_id=resource_id,
        occurred_at=now or datetime.now(tz=timezone.utc),
        trace_id=trace_id,
        ip_address=ip_address,
        outcome=outcome,
        detail=redact_sensitive(detail),
    )
    session.add(row)
    await session.flush()
    return row
