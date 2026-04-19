import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentRequirement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_requirements"
    __table_args__ = (
        UniqueConstraint("requirement_code", name="uq_doc_requirement_code"),
    )

    requirement_code: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_mime_types: Mapped[str] = mapped_column(
        String(500), default="application/pdf,image/jpeg,image/png", nullable=False
    )
    max_size_bytes: Mapped[int] = mapped_column(
        BigInteger, default=25 * 1024 * 1024, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ChecklistTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "checklist_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    program_code: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    items: Mapped[list["ChecklistTemplateItem"]] = relationship(back_populates="template")


class ChecklistTemplateItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "checklist_template_items"
    __table_args__ = (
        UniqueConstraint("template_id", "requirement_id", name="uq_checklist_tmpl_req"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checklist_templates.id", ondelete="CASCADE"), nullable=False
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_requirements.id", ondelete="RESTRICT"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    template: Mapped["ChecklistTemplate"] = relationship(back_populates="items")


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_candidate_id", "candidate_id"),
        Index("ix_documents_document_type", "document_type"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_requirements.id", ondelete="SET NULL")
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_status: Mapped[str] = mapped_column(
        String(50), default="pending_review", nullable=False
    )
    resubmission_reason: Mapped[str | None] = mapped_column(Text)

    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document")
    reviews: Mapped[list["DocumentReview"]] = relationship(back_populates="document")
    access_grants: Mapped[list["DocumentAccessGrant"]] = relationship(back_populates="document")


class DocumentVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
        Index("ix_doc_versions_document_id", "document_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="versions")
    reviews: Mapped[list["DocumentReview"]] = relationship(back_populates="version")


class DocumentReview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_reviews"
    __table_args__ = (
        Index("ix_doc_reviews_document_id", "document_id"),
        Index("ix_doc_reviews_version_id", "version_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    resubmission_reason: Mapped[str | None] = mapped_column(Text)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="reviews")
    version: Mapped["DocumentVersion"] = relationship(back_populates="reviews")


class DocumentAccessGrant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_access_grants"
    __table_args__ = (
        UniqueConstraint("document_id", "granted_role", name="uq_doc_access_role"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    granted_role: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="access_grants")
