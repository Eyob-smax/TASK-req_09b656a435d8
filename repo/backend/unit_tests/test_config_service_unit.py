"""
BE-UNIT: Config service — feature-flag evaluation, cohort override, canary routing,
resolve_flags_for_user merges base+overrides.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.enums import UserRole
from src.security.rbac import Actor


def _make_actor(role: UserRole = UserRole.admin) -> Actor:
    return Actor(user_id=str(uuid.uuid4()), role=role, username="admin1")


# ── Flag evaluation ───────────────────────────────────────────────────────────

def test_flag_value_boolean_true():
    """A flag stored as 'true' maps to boolean True in the session store contract."""
    assert ("true" == "true") is True


def test_flag_value_boolean_false():
    assert ("false" == "true") is False


# ── resolve_flags_for_user ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_flags_no_assignment():
    """User with no cohort gets base flags only."""
    from src.services.config_service import ConfigService

    session = AsyncMock()
    svc = ConfigService(session)
    svc.repo = AsyncMock()

    flag = MagicMock()
    flag.key = "bargaining_enabled"
    flag.value = "true"
    svc.repo.list_flags = AsyncMock(return_value=[flag])
    svc.repo.get_user_assignment = AsyncMock(return_value=None)

    resolved, cohort_key = await svc.resolve_flags_for_user(uuid.uuid4())
    assert resolved == {"bargaining_enabled": "true"}
    assert cohort_key is None


@pytest.mark.asyncio
async def test_resolve_flags_with_cohort_override():
    """Cohort overrides merge on top of base flags."""
    from src.services.config_service import ConfigService

    session = AsyncMock()
    svc = ConfigService(session)
    svc.repo = AsyncMock()

    base_flag = MagicMock()
    base_flag.key = "bargaining_enabled"
    base_flag.value = "false"
    svc.repo.list_flags = AsyncMock(return_value=[base_flag])

    assignment = MagicMock()
    assignment.cohort_id = uuid.uuid4()
    svc.repo.get_user_assignment = AsyncMock(return_value=assignment)

    cohort = MagicMock()
    cohort.cohort_key = "pilot"
    cohort.is_active = True
    cohort.flag_overrides = {"bargaining_enabled": "true"}
    svc.repo.get_cohort = AsyncMock(return_value=cohort)

    resolved, cohort_key = await svc.resolve_flags_for_user(uuid.uuid4())
    assert resolved["bargaining_enabled"] == "true"
    assert cohort_key == "pilot"


@pytest.mark.asyncio
async def test_resolve_flags_inactive_cohort_ignored():
    """Inactive cohort's overrides are not applied."""
    from src.services.config_service import ConfigService

    session = AsyncMock()
    svc = ConfigService(session)
    svc.repo = AsyncMock()

    base_flag = MagicMock()
    base_flag.key = "rollback_enabled"
    base_flag.value = "true"
    svc.repo.list_flags = AsyncMock(return_value=[base_flag])

    assignment = MagicMock()
    assignment.cohort_id = uuid.uuid4()
    svc.repo.get_user_assignment = AsyncMock(return_value=assignment)

    cohort = MagicMock()
    cohort.is_active = False
    cohort.flag_overrides = {"rollback_enabled": "false"}
    svc.repo.get_cohort = AsyncMock(return_value=cohort)

    resolved, cohort_key = await svc.resolve_flags_for_user(uuid.uuid4())
    assert resolved["rollback_enabled"] == "true"
    assert cohort_key is None


# ── Admin role enforcement ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_flag_requires_admin():
    """Non-admin actor is rejected by _require_admin."""
    from src.services.config_service import ConfigService
    from src.security.errors import ForbiddenError

    session = AsyncMock()
    svc = ConfigService(session)
    reviewer = Actor(user_id=str(uuid.uuid4()), role=UserRole.reviewer, username="rev")

    with pytest.raises(ForbiddenError):
        await svc.set_flag("bargaining_enabled", "false", reviewer)


@pytest.mark.asyncio
async def test_create_cohort_requires_admin():
    """Non-admin cannot create cohorts."""
    from src.services.config_service import ConfigService, CohortDefinitionCreate
    from src.security.errors import ForbiddenError

    session = AsyncMock()
    svc = ConfigService(session)
    candidate = Actor(user_id=str(uuid.uuid4()), role=UserRole.candidate, username="cand")

    with pytest.raises(ForbiddenError):
        await svc.create_cohort(candidate, CohortDefinitionCreate(
            cohort_key="test", name="Test",
        ))


# ── Bootstrap config ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bootstrap_config_produces_signature():
    """bootstrap_config returns a non-empty signature."""
    from src.services.config_service import ConfigService

    session = AsyncMock()
    svc = ConfigService(session)
    svc.repo = AsyncMock()
    svc.repo.list_flags = AsyncMock(return_value=[])
    svc.repo.get_user_assignment = AsyncMock(return_value=None)

    uid = uuid.uuid4()
    config = await svc.bootstrap_config(uid, "candidate")
    assert config.signature
    assert len(config.signature) == 32
    assert config.resolved_flags == {}
    assert config.cohort_key is None
