"""
BE-UNIT: Export policy — admin-only access, watermark applied, SHA-256 stored.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest

from src.domain.enums import UserRole
from src.security.rbac import Actor


def _make_actor(role: UserRole) -> Actor:
    return Actor(user_id=str(uuid.uuid4()), role=role, username="user1")


# ── Admin-only enforcement ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_export_admin_only():
    """Reviewer cannot create export jobs."""
    from src.services.export_service import ExportService
    from src.security.errors import ForbiddenError

    session = AsyncMock()
    svc = ExportService(session)
    reviewer = _make_actor(UserRole.reviewer)

    with pytest.raises(ForbiddenError):
        await svc.create_export_job(reviewer, "audit_csv")


@pytest.mark.asyncio
async def test_list_exports_admin_only():
    """Candidate cannot list exports."""
    from src.services.export_service import ExportService
    from src.security.errors import ForbiddenError

    session = AsyncMock()
    svc = ExportService(session)
    candidate = _make_actor(UserRole.candidate)

    with pytest.raises(ForbiddenError):
        await svc.list_export_jobs(candidate)


@pytest.mark.asyncio
async def test_download_export_admin_only():
    """Non-admin cannot download exports."""
    from src.services.export_service import ExportService
    from src.security.errors import ForbiddenError

    session = AsyncMock()
    svc = ExportService(session)
    reviewer = _make_actor(UserRole.reviewer)

    with pytest.raises(ForbiddenError):
        await svc.download_export(uuid.uuid4(), reviewer)


# ── SHA-256 stored on completion ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_stores_sha256():
    """After successful export, job record has a non-empty sha256_hash."""
    from src.services.export_service import ExportService

    session = AsyncMock()
    svc = ExportService(session)
    admin = _make_actor(UserRole.admin)

    job = MagicMock()
    job.id = uuid.uuid4()
    job.export_type = "audit_csv"
    job.created_at = datetime.now(tz=timezone.utc)

    svc.repo = AsyncMock()
    svc.repo.create_export_job = AsyncMock(return_value=job)
    svc.repo.update_export_job = AsyncMock()

    csv_bytes = b"id,event_type\n1,login_success\n"

    with patch.object(svc, '_generate_content', AsyncMock(return_value=csv_bytes)):
        with patch.object(svc, '_persist', AsyncMock(return_value="/tmp/export.csv")):
            await svc.create_export_job(admin, "audit_csv")

    update_call = svc.repo.update_export_job.call_args
    assert update_call.kwargs.get("sha256_hash") is not None
    assert len(update_call.kwargs["sha256_hash"]) == 64  # SHA-256 hex


# ── Watermark recorded ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_records_watermark_username():
    """Completed export records watermark_username in repo update call."""
    from src.services.export_service import ExportService

    session = AsyncMock()
    svc = ExportService(session)
    admin = _make_actor(UserRole.admin)
    admin = Actor(user_id=str(uuid.uuid4()), role=UserRole.admin, username="carol_admin")

    job = MagicMock()
    job.id = uuid.uuid4()
    job.export_type = "audit_csv"
    job.created_at = datetime.now(tz=timezone.utc)

    svc.repo = AsyncMock()
    svc.repo.create_export_job = AsyncMock(return_value=job)
    svc.repo.update_export_job = AsyncMock()

    csv_bytes = b"id\n1\n"
    with patch.object(svc, '_generate_content', AsyncMock(return_value=csv_bytes)):
        with patch.object(svc, '_persist', AsyncMock(return_value="/tmp/export.csv")):
            await svc.create_export_job(admin, "audit_csv")

    update_call = svc.repo.update_export_job.call_args
    assert update_call.kwargs.get("watermark_username") == "carol_admin"
    assert update_call.kwargs.get("watermark_applied") is True


# ── RBAC policy static values ─────────────────────────────────────────────────

def test_download_approved_roles_include_reviewer_and_admin():
    from src.security.rbac import DOWNLOAD_APPROVED_ROLES
    assert UserRole.reviewer in DOWNLOAD_APPROVED_ROLES
    assert UserRole.admin in DOWNLOAD_APPROVED_ROLES
    assert UserRole.candidate not in DOWNLOAD_APPROVED_ROLES


def test_privileged_roles_include_reviewer_and_admin():
    from src.security.rbac import PRIVILEGED_ROLES
    assert UserRole.reviewer in PRIVILEGED_ROLES
    assert UserRole.admin in PRIVILEGED_ROLES


def test_masking_applied_to_non_privileged():
    from src.security.data_masking import mask_ssn, mask_email, is_privileged
    assert not is_privileged(UserRole.candidate)
    assert mask_ssn("123456789") == "***-**-6789"
    assert mask_email("alice@example.com") == "***@example.com"
