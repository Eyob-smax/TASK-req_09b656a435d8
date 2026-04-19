from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.attendance import (
    AttendanceAnomaly,
    AttendanceException,
    ExceptionApproval,
    ExceptionProof,
    ExceptionReviewStep,
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class AttendanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Anomalies ────────────────────────────────────────────────────────────

    async def create_anomaly(
        self,
        candidate_id: uuid.UUID,
        anomaly_type: str,
        session_date: datetime,
        flagged_by: uuid.UUID,
        session_identifier: str | None = None,
        description: str | None = None,
    ) -> AttendanceAnomaly:
        anomaly = AttendanceAnomaly(
            candidate_id=candidate_id,
            anomaly_type=anomaly_type,
            session_date=session_date,
            flagged_by=flagged_by,
            flagged_at=_now(),
            session_identifier=session_identifier,
            description=description,
        )
        self.session.add(anomaly)
        await self.session.flush()
        return anomaly

    async def get_anomaly(self, anomaly_id: uuid.UUID) -> AttendanceAnomaly | None:
        return await self.session.get(AttendanceAnomaly, anomaly_id)

    async def list_anomalies(
        self, candidate_id: uuid.UUID | None = None
    ) -> list[AttendanceAnomaly]:
        q = select(AttendanceAnomaly)
        if candidate_id is not None:
            q = q.where(AttendanceAnomaly.candidate_id == candidate_id)
        return list((await self.session.execute(q)).scalars().all())

    # ── Exceptions ────────────────────────────────────────────────────────────

    async def create_exception(
        self,
        candidate_id: uuid.UUID,
        current_stage: str,
        anomaly_id: uuid.UUID | None = None,
        candidate_statement: str | None = None,
    ) -> AttendanceException:
        exc = AttendanceException(
            anomaly_id=anomaly_id,
            candidate_id=candidate_id,
            status="pending_proof",
            current_stage=current_stage,
            candidate_statement=candidate_statement,
        )
        self.session.add(exc)
        await self.session.flush()
        return exc

    async def get_exception(
        self, exception_id: uuid.UUID
    ) -> AttendanceException | None:
        q = (
            select(AttendanceException)
            .options(
                selectinload(AttendanceException.proofs),
                selectinload(AttendanceException.review_steps).selectinload(
                    ExceptionReviewStep.approval
                ),
            )
            .where(AttendanceException.id == exception_id)
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_exceptions(
        self,
        candidate_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AttendanceException], int]:
        q = select(AttendanceException).options(
            selectinload(AttendanceException.review_steps)
        )
        if candidate_id is not None:
            q = q.where(AttendanceException.candidate_id == candidate_id)
        if status is not None:
            q = q.where(AttendanceException.status == status)
        total = (
            await self.session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()
        q = q.offset((page - 1) * page_size).limit(page_size)
        exceptions = list((await self.session.execute(q)).scalars().all())
        return exceptions, total

    async def update_exception_status(
        self,
        exception: AttendanceException,
        new_status: str,
        current_stage: str | None = None,
    ) -> None:
        exception.status = new_status
        if current_stage is not None:
            exception.current_stage = current_stage
        await self.session.flush()

    # ── Proofs ────────────────────────────────────────────────────────────────

    async def add_proof(
        self,
        exception_id: uuid.UUID,
        document_version_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        description: str | None = None,
    ) -> ExceptionProof:
        proof = ExceptionProof(
            exception_id=exception_id,
            document_version_id=document_version_id,
            uploaded_by=uploaded_by,
            uploaded_at=_now(),
            description=description,
        )
        self.session.add(proof)
        await self.session.flush()
        return proof

    # ── Review steps ──────────────────────────────────────────────────────────

    async def add_review_step(
        self,
        exception_id: uuid.UUID,
        step_order: int,
        stage: str,
        reviewer_id: uuid.UUID,
        reviewer_role: str,
        decision: str,
        notes: str | None,
        is_escalated: bool,
    ) -> ExceptionReviewStep:
        step = ExceptionReviewStep(
            exception_id=exception_id,
            step_order=step_order,
            stage=stage,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            decision=decision,
            notes=notes,
            decided_at=_now(),
            is_escalated=is_escalated,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def add_approval(
        self,
        step_id: uuid.UUID,
        exception_id: uuid.UUID,
        approved_by: uuid.UUID,
        outcome: str,
        signature_hash: str | None,
    ) -> ExceptionApproval:
        approval = ExceptionApproval(
            step_id=step_id,
            exception_id=exception_id,
            approved_by=approved_by,
            approved_at=_now(),
            outcome=outcome,
            signature_hash=signature_hash,
        )
        self.session.add(approval)
        await self.session.flush()
        return approval

    # ── Queue helpers ─────────────────────────────────────────────────────────

    async def pending_initial_review(self) -> list[AttendanceException]:
        q = select(AttendanceException).where(
            AttendanceException.status == "pending_initial_review"
        )
        return list((await self.session.execute(q)).scalars().all())

    async def pending_final_review(self) -> list[AttendanceException]:
        q = select(AttendanceException).where(
            AttendanceException.status == "pending_final_review"
        )
        return list((await self.session.execute(q)).scalars().all())
