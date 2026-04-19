"""
Column-level masking helpers.

Schemas use `@field_serializer` with access to a `SerializationContext`
passed through `model_dump(context=...)`. If the actor role is privileged,
the plaintext value is emitted; otherwise a masked form is produced.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..domain.enums import UserRole
from .rbac import PRIVILEGED_ROLES


@dataclass(frozen=True)
class SerializationContext:
    actor_role: UserRole | None = None
    is_self: bool = False

    @property
    def privileged(self) -> bool:
        if self.actor_role is None:
            return False
        return self.actor_role in PRIVILEGED_ROLES


def is_privileged(role: UserRole | str | None) -> bool:
    if role is None:
        return False
    if isinstance(role, str):
        try:
            role = UserRole(role)
        except ValueError:
            return False
    return role in PRIVILEGED_ROLES


def mask_ssn(value: str | None) -> str | None:
    if not value:
        return value
    tail = value[-4:] if len(value) >= 4 else value
    return f"***-**-{tail}"


def mask_dob(value) -> str | None:
    """Accept either a string 'YYYY-MM-DD' or a date/datetime; return year only."""
    if value is None:
        return None
    text = str(value)
    if len(text) >= 4 and text[:4].isdigit():
        return f"{text[:4]}-**-**"
    return "****-**-**"


def mask_phone(value: str | None) -> str | None:
    if not value:
        return value
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***-***-{digits[-4:]}"


def mask_email(value: str | None) -> str | None:
    if not value or "@" not in value:
        return value
    _, _, domain = value.partition("@")
    return f"***@{domain}"


def resolve_context(context: object) -> SerializationContext:
    """Normalize a possibly-None context argument."""
    if context is None:
        return SerializationContext()
    if isinstance(context, SerializationContext):
        return context
    if isinstance(context, dict):
        role = context.get("actor_role")
        if isinstance(role, str):
            try:
                role = UserRole(role)
            except ValueError:
                role = None
        return SerializationContext(
            actor_role=role if isinstance(role, UserRole) else None,
            is_self=bool(context.get("is_self", False)),
        )
    return SerializationContext()
