"""
RBAC primitives: Actor, role assertions, ownership, row scoping, dependency factory.
"""
import pytest

from src.domain.enums import UserRole
from src.security.errors import ForbiddenError, OwnershipError
from src.security.rbac import (
    Actor,
    DOWNLOAD_APPROVED_ROLES,
    assert_owner,
    assert_role,
    assert_roles_or_owner,
    can_download_restricted,
    has_role,
    require_role,
    scope_rows_to_actor,
)


def _actor(role: UserRole, user_id: str = "u-1") -> Actor:
    return Actor(user_id=user_id, role=role, username="alice")


def test_has_role_positive():
    assert has_role(_actor(UserRole.reviewer), [UserRole.reviewer, UserRole.admin])


def test_has_role_negative():
    assert not has_role(_actor(UserRole.candidate), [UserRole.admin])


def test_assert_role_rejects_wrong_role():
    with pytest.raises(ForbiddenError):
        assert_role(_actor(UserRole.candidate), [UserRole.admin])


def test_assert_role_allows_correct_role():
    assert_role(_actor(UserRole.admin), [UserRole.admin])


def test_assert_owner_mismatch_raises():
    with pytest.raises(OwnershipError):
        assert_owner(_actor(UserRole.candidate, user_id="u-1"), owner_id="u-2")


def test_assert_owner_matching_id_passes():
    assert_owner(_actor(UserRole.candidate, user_id="u-1"), owner_id="u-1")


def test_assert_roles_or_owner_allows_role_bypass():
    assert_roles_or_owner(_actor(UserRole.admin, user_id="u-2"), [UserRole.admin], owner_id="u-1")


def test_assert_roles_or_owner_allows_owner_bypass():
    assert_roles_or_owner(_actor(UserRole.candidate, user_id="u-1"), [UserRole.admin], owner_id="u-1")


def test_assert_roles_or_owner_rejects_stranger():
    with pytest.raises(ForbiddenError):
        assert_roles_or_owner(
            _actor(UserRole.candidate, user_id="u-2"), [UserRole.admin], owner_id="u-1"
        )


def test_require_role_dependency_accepts():
    dep = require_role(UserRole.admin)
    assert dep(_actor(UserRole.admin)).role == UserRole.admin


def test_require_role_dependency_rejects():
    dep = require_role(UserRole.admin)
    with pytest.raises(ForbiddenError):
        dep(_actor(UserRole.candidate))


def test_scope_rows_candidate_adds_where_clause():
    from sqlalchemy import Column, Integer, String, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class _Base(DeclarativeBase):
        pass

    class _Doc(_Base):
        __tablename__ = "_doc_scope_test"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        owner_id: Mapped[str] = mapped_column(String(40))

    base = select(_Doc)
    scoped = scope_rows_to_actor(base, _actor(UserRole.candidate), _Doc.owner_id)
    compiled = str(scoped.compile(compile_kwargs={"literal_binds": True}))
    assert "owner_id" in compiled

    unscoped = scope_rows_to_actor(base, _actor(UserRole.admin), _Doc.owner_id)
    assert str(unscoped.compile()) == str(base.compile())


def test_download_approved_roles_gate():
    assert can_download_restricted(UserRole.reviewer) is True
    assert can_download_restricted(UserRole.admin) is True
    assert can_download_restricted(UserRole.candidate) is False
    assert UserRole.proctor not in DOWNLOAD_APPROVED_ROLES
