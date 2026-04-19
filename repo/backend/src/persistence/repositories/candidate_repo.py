from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.candidate import (
    CandidateProfile,
    ExamScore,
    ProfileHistory,
    TransferPreference,
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class CandidateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Profile ──────────────────────────────────────────────────────────────

    async def list_paginated(
        self, page: int, page_size: int
    ) -> tuple[list[CandidateProfile], int]:
        offset = (page - 1) * page_size
        total_q = await self.session.execute(
            select(func.count()).select_from(CandidateProfile).where(
                CandidateProfile.deleted_at.is_(None)
            )
        )
        total = total_q.scalar_one()
        rows_q = await self.session.execute(
            select(CandidateProfile)
            .where(CandidateProfile.deleted_at.is_(None))
            .order_by(CandidateProfile.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(rows_q.scalars().all()), total

    async def get_by_user_id(self, user_id: uuid.UUID) -> CandidateProfile | None:
        q = select(CandidateProfile).where(
            CandidateProfile.user_id == user_id,
            CandidateProfile.deleted_at.is_(None),
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def get_by_id(self, candidate_id: uuid.UUID) -> CandidateProfile | None:
        q = select(CandidateProfile).where(
            CandidateProfile.id == candidate_id,
            CandidateProfile.deleted_at.is_(None),
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, **fields) -> CandidateProfile:
        profile = CandidateProfile(user_id=user_id, **fields)
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update(self, profile: CandidateProfile, **fields) -> None:
        for key, value in fields.items():
            setattr(profile, key, value)
        await self.session.flush()

    # ── Exam scores ───────────────────────────────────────────────────────────

    async def list_exam_scores(self, candidate_id: uuid.UUID) -> list[ExamScore]:
        q = select(ExamScore).where(ExamScore.candidate_id == candidate_id)
        return list((await self.session.execute(q)).scalars().all())

    async def add_exam_score(self, candidate_id: uuid.UUID, **fields) -> ExamScore:
        score = ExamScore(candidate_id=candidate_id, **fields)
        self.session.add(score)
        await self.session.flush()
        return score

    async def get_exam_score(self, score_id: uuid.UUID) -> ExamScore | None:
        return await self.session.get(ExamScore, score_id)

    # ── Transfer preferences ──────────────────────────────────────────────────

    async def list_transfer_preferences(
        self, candidate_id: uuid.UUID
    ) -> list[TransferPreference]:
        q = select(TransferPreference).where(
            TransferPreference.candidate_id == candidate_id
        )
        return list((await self.session.execute(q)).scalars().all())

    async def add_transfer_preference(
        self, candidate_id: uuid.UUID, **fields
    ) -> TransferPreference:
        pref = TransferPreference(candidate_id=candidate_id, **fields)
        self.session.add(pref)
        await self.session.flush()
        return pref

    async def get_transfer_preference(
        self, pref_id: uuid.UUID
    ) -> TransferPreference | None:
        return await self.session.get(TransferPreference, pref_id)

    async def update_transfer_preference(
        self, pref: TransferPreference, **fields
    ) -> None:
        for key, value in fields.items():
            setattr(pref, key, value)
        await self.session.flush()

    # ── Profile history ───────────────────────────────────────────────────────

    async def add_profile_history(
        self,
        candidate_id: uuid.UUID,
        changed_by: uuid.UUID,
        field_name: str,
        old_value_encrypted: str | None,
        new_value_encrypted: str | None,
        change_reason: str | None = None,
    ) -> None:
        entry = ProfileHistory(
            candidate_id=candidate_id,
            changed_by=changed_by,
            changed_at=_now(),
            field_name=field_name,
            old_value_encrypted=old_value_encrypted,
            new_value_encrypted=new_value_encrypted,
            change_reason=change_reason,
        )
        self.session.add(entry)
        await self.session.flush()
