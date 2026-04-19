"""
Export service: generates watermarked CSV/PDF exports, tracks jobs, enforces admin-only access.

Exports are created synchronously (small datasets) — no async job queue needed
for local deployment scale. SHA-256 is computed and stored with each job for
integrity verification on download.
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..domain.enums import AuditEventType, UserRole
from ..persistence.repositories.config_repo import ConfigRepository
from ..schemas.audit import ExportJobRead
from ..security import audit as audit_mod
from ..security.errors import ForbiddenError, ResourceNotFoundError
from ..security.hashing import sha256_of_bytes
from ..security.watermark import apply_pdf_watermark
from ..security.rbac import Actor


def _require_admin(actor: Actor) -> None:
    if actor.role != UserRole.admin:
        raise ForbiddenError("Admin role required for export operations.")


def _job_to_schema(job) -> ExportJobRead:
    return ExportJobRead(
        id=job.id,
        requested_by=job.requested_by,
        export_type=job.export_type,
        status=job.status,
        sha256_hash=job.sha256_hash,
        watermark_applied=job.watermark_applied,
        completed_at=job.completed_at,
        created_at=job.created_at,
    )


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ConfigRepository(session)
        self.settings = get_settings()

    async def create_export_job(
        self, actor: Actor, export_type: str, filters: dict | None = None
    ) -> ExportJobRead:
        _require_admin(actor)
        job = await self.repo.create_export_job(
            requested_by=uuid.UUID(actor.user_id),
            export_type=export_type,
        )
        now = datetime.now(tz=timezone.utc)
        try:
            content = await self._generate_content(export_type, filters, actor)
            sha256 = sha256_of_bytes(content)
            storage_path = await self._persist(job.id, export_type, content)
            await self.repo.update_export_job(
                job,
                status="completed",
                storage_path=storage_path,
                sha256_hash=sha256,
                watermark_applied=True,
                watermark_username=actor.username,
                watermark_timestamp=now,
                completed_at=now,
            )
        except Exception as exc:
            await self.repo.update_export_job(
                job,
                status="failed",
                error_message=str(exc)[:500],
                completed_at=now,
            )
            raise
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.export_generated,
            actor_id=uuid.UUID(actor.user_id),
            actor_role=actor.role.value,
            resource_type="export_job",
            resource_id=str(job.id),
            outcome="success",
            detail={"export_type": export_type, "sha256": sha256},
        )
        return _job_to_schema(job)

    async def list_export_jobs(
        self, actor: Actor, page: int = 1, page_size: int = 20
    ) -> tuple[list[ExportJobRead], int]:
        _require_admin(actor)
        jobs, total = await self.repo.list_export_jobs(page=page, page_size=page_size)
        return [_job_to_schema(j) for j in jobs], total

    async def download_export(self, export_id: uuid.UUID, actor: Actor) -> tuple[bytes, str]:
        _require_admin(actor)
        job = await self.repo.get_export_job(export_id)
        if job is None:
            raise ResourceNotFoundError("Export job not found.")
        if job.status != "completed" or not job.storage_path:
            raise ResourceNotFoundError("Export not yet available.")
        path = Path(job.storage_path)
        if not path.exists():
            raise ResourceNotFoundError("Export file not found on disk.")
        content = path.read_bytes()
        await audit_mod.record_audit(
            self.session,
            event_type=AuditEventType.document_downloaded,
            actor_id=uuid.UUID(actor.user_id),
            actor_role=actor.role.value,
            resource_type="export_job",
            resource_id=str(export_id),
            outcome="success",
        )
        ext = "csv" if job.export_type.endswith("csv") or "csv" in job.export_type else "pdf"
        return content, f'attachment; filename="export_{export_id}.{ext}"'

    async def _generate_content(
        self, export_type: str, filters: dict | None, actor: Actor
    ) -> bytes:
        """Generate CSV content from audit events or other sources."""
        from ..persistence.models.config_audit import AuditEvent
        from sqlalchemy import select

        watermark_line = (
            f"# WATERMARK | exported_by={actor.username}"
            f" | timestamp={datetime.now(timezone.utc).isoformat()}\n"
        )

        if export_type in ("audit_csv", "audit"):
            q = select(AuditEvent).order_by(AuditEvent.occurred_at.desc()).limit(10000)
            rows = list((await self.session.execute(q)).scalars().all())
            buf = io.StringIO()
            writer = csv.DictWriter(
                buf,
                fieldnames=["id", "event_type", "actor_id", "actor_role",
                            "resource_type", "resource_id", "outcome", "occurred_at", "trace_id"],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    "id": str(row.id),
                    "event_type": row.event_type,
                    "actor_id": str(row.actor_id) if row.actor_id else "",
                    "actor_role": row.actor_role or "",
                    "resource_type": row.resource_type or "",
                    "resource_id": row.resource_id or "",
                    "outcome": row.outcome,
                    "occurred_at": row.occurred_at.isoformat(),
                    "trace_id": row.trace_id or "",
                })
            return (watermark_line + buf.getvalue()).encode("utf-8")

        if export_type in ("forecast_csv", "forecast"):
            from ..persistence.models.config_audit import ForecastSnapshot
            from sqlalchemy import select as sa_select
            q = sa_select(ForecastSnapshot).order_by(ForecastSnapshot.computed_at.desc()).limit(100)
            snaps = list((await self.session.execute(q)).scalars().all())
            buf = io.StringIO()
            writer = csv.DictWriter(
                buf,
                fieldnames=["id", "computed_at", "horizon_days", "input_window_days",
                            "bandwidth_p50_bytes", "bandwidth_p95_bytes", "notes"],
            )
            writer.writeheader()
            for s in snaps:
                writer.writerow({
                    "id": str(s.id),
                    "computed_at": s.computed_at.isoformat(),
                    "horizon_days": s.forecast_horizon_days,
                    "input_window_days": s.input_window_days,
                    "bandwidth_p50_bytes": s.bandwidth_p50_bytes or 0,
                    "bandwidth_p95_bytes": s.bandwidth_p95_bytes or 0,
                    "notes": s.notes or "",
                })
            return (watermark_line + buf.getvalue()).encode("utf-8")

        raise ValueError(f"Unknown export_type: {export_type}")

    async def _persist(self, job_id: uuid.UUID, export_type: str, content: bytes) -> str:
        ext = "csv"
        root = Path(self.settings.exports_root)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{job_id}_{export_type}.{ext}"
        path.write_bytes(content)
        return str(path)
