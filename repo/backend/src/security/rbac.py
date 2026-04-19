"""
Role-Based Access Control primitives.

Four enforcement layers:
    - route / function: `require_role(*roles)` as a FastAPI dependency
    - object:           `assert_owner(actor, owner_id)` and `assert_roles_or_owner`
    - row:              `scope_rows_to_actor(query, actor, owner_column)`
    - column:           `data_masking.is_privileged(role)` used by schema serializers
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..domain.enums import UserRole
from .errors import ForbiddenError, OwnershipError

DOWNLOAD_APPROVED_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.reviewer, UserRole.admin}
)

PRIVILEGED_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.reviewer, UserRole.admin}
)


@dataclass(frozen=True)
class Actor:
    user_id: str
    role: UserRole
    username: str


def coerce_role(value: str | UserRole) -> UserRole:
    if isinstance(value, UserRole):
        return value
    return UserRole(value)


def has_role(actor: Actor, roles: Iterable[UserRole | str]) -> bool:
    wanted = {coerce_role(r) for r in roles}
    return actor.role in wanted


def assert_role(actor: Actor, roles: Iterable[UserRole | str]) -> None:
    if not has_role(actor, roles):
        raise ForbiddenError("Role is not permitted to perform this action.")


def assert_owner(actor: Actor, owner_id: str) -> None:
    if str(actor.user_id) != str(owner_id):
        raise OwnershipError("Actor is not the owner of this resource.")


def assert_roles_or_owner(
    actor: Actor,
    roles: Iterable[UserRole | str],
    owner_id: str,
) -> None:
    if has_role(actor, roles):
        return
    if str(actor.user_id) == str(owner_id):
        return
    raise ForbiddenError("Actor is neither privileged nor the resource owner.")


def scope_rows_to_actor(query, actor: Actor, owner_column):
    """Row-level filter: candidates see only their own rows; staff see all."""
    if actor.role == UserRole.candidate:
        return query.where(owner_column == actor.user_id)
    return query


def require_role(*roles: UserRole | str):
    """FastAPI dependency factory enforcing route-level role gating."""
    wanted = [coerce_role(r) for r in roles]

    def _dep(actor: Actor):
        if actor.role not in wanted:
            raise ForbiddenError("Role is not permitted for this route.")
        return actor

    return _dep


def can_download_restricted(role: UserRole) -> bool:
    return role in DOWNLOAD_APPROVED_ROLES
