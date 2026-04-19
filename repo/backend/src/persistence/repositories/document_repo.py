from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import (
    ChecklistTemplate,
    ChecklistTemplateItem,
    Document,
    DocumentAccessGrant,
    DocumentRequirement,
    DocumentReview,
    DocumentVersion,
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Requirements ─────────────────────────────────────────────────────────

    async def get_requirement(
        self, requirement_id: uuid.UUID
    ) -> DocumentRequirement | None:
        return await self.session.get(DocumentRequirement, requirement_id)

    async def get_requirement_by_code(self, code: str) -> DocumentRequirement | None:
        q = select(DocumentRequirement).where(
            DocumentRequirement.requirement_code == code,
            DocumentRequirement.is_active.is_(True),
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_requirements(self) -> list[DocumentRequirement]:
        q = select(DocumentRequirement).where(DocumentRequirement.is_active.is_(True))
        return list((await self.session.execute(q)).scalars().all())

    # ── Documents ─────────────────────────────────────────────────────────────

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        q = (
            select(Document)
            .options(
                selectinload(Document.versions),
                selectinload(Document.reviews),
            )
            .where(Document.id == document_id)
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def list_candidate_documents(
        self, candidate_id: uuid.UUID
    ) -> list[Document]:
        q = (
            select(Document)
            .options(selectinload(Document.versions))
            .where(Document.candidate_id == candidate_id)
        )
        return list((await self.session.execute(q)).scalars().all())

    async def create_document(
        self,
        candidate_id: uuid.UUID,
        requirement_id: uuid.UUID | None,
        document_type: str,
    ) -> Document:
        doc = Document(
            candidate_id=candidate_id,
            requirement_id=requirement_id,
            document_type=document_type,
            current_version=0,
            current_status="pending_review",
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def add_version(
        self,
        document: Document,
        original_filename: str,
        stored_filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        sha256_hash: str,
        uploaded_by: uuid.UUID,
    ) -> DocumentVersion:
        document.current_version += 1
        version = DocumentVersion(
            document_id=document.id,
            version_number=document.current_version,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
            uploaded_by=uploaded_by,
            uploaded_at=_now(),
            is_active=True,
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def update_document_status(
        self,
        document: Document,
        new_status: str,
        resubmission_reason: str | None = None,
    ) -> None:
        document.current_status = new_status
        if resubmission_reason is not None:
            document.resubmission_reason = resubmission_reason
        elif new_status != "needs_resubmission":
            document.resubmission_reason = None
        await self.session.flush()

    async def add_review(
        self,
        document_id: uuid.UUID,
        version_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        status: str,
        resubmission_reason: str | None,
        reviewer_notes: str | None,
    ) -> DocumentReview:
        review = DocumentReview(
            document_id=document_id,
            version_id=version_id,
            reviewer_id=reviewer_id,
            status=status,
            resubmission_reason=resubmission_reason,
            reviewer_notes=reviewer_notes,
            decided_at=_now(),
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def get_version(self, version_id: uuid.UUID) -> DocumentVersion | None:
        return await self.session.get(DocumentVersion, version_id)

    async def get_latest_version(self, document: Document) -> DocumentVersion | None:
        q = select(DocumentVersion).where(
            DocumentVersion.document_id == document.id,
            DocumentVersion.version_number == document.current_version,
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    # ── Checklist ─────────────────────────────────────────────────────────────

    async def get_checklist(self, candidate_id: uuid.UUID) -> list[dict]:
        """
        Returns a list of dicts describing each active document requirement
        and the candidate's latest document status for it (if any).
        """
        reqs = await self.list_requirements()
        if not reqs:
            return []

        candidate_docs = await self.list_candidate_documents(candidate_id)
        req_to_doc: dict[uuid.UUID, Document] = {}
        for doc in candidate_docs:
            if doc.requirement_id and doc.requirement_id not in req_to_doc:
                req_to_doc[doc.requirement_id] = doc

        items = []
        for req in reqs:
            doc = req_to_doc.get(req.id)
            items.append(
                {
                    "requirement_id": req.id,
                    "requirement_code": req.requirement_code,
                    "display_name": req.display_name,
                    "is_mandatory": req.is_mandatory,
                    "status": doc.current_status if doc else None,
                    "document_id": doc.id if doc else None,
                    "version_number": doc.current_version if doc else None,
                }
            )
        return items
