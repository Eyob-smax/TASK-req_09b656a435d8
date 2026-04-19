import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from ..domain.enums import DocumentStatus


class DocumentRequirementRead(BaseModel):
    id: uuid.UUID
    requirement_code: str
    display_name: str
    description: str | None
    is_mandatory: bool
    allowed_mime_types: list[str]
    max_size_bytes: int


class ChecklistItemRead(BaseModel):
    requirement_id: uuid.UUID
    requirement_code: str
    display_name: str
    is_mandatory: bool
    status: DocumentStatus | None
    document_id: uuid.UUID | None
    version_number: int | None


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    version_number: int
    original_filename: str
    content_type: str
    size_bytes: int
    sha256_hash: str
    status: DocumentStatus
    uploaded_at: datetime


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    original_filename: str
    content_type: str
    size_bytes: int
    sha256_hash: str
    uploaded_by: uuid.UUID
    uploaded_at: datetime
    is_active: bool


class DocumentReviewRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_id: uuid.UUID
    reviewer_id: uuid.UUID
    status: DocumentStatus
    resubmission_reason: str | None
    reviewer_notes: str | None
    decided_at: datetime
    created_at: datetime


class DocumentReviewCreate(BaseModel):
    version_id: uuid.UUID
    status: DocumentStatus
    resubmission_reason: str | None = Field(None, max_length=2000)
    reviewer_notes: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def resubmission_reason_required(self) -> "DocumentReviewCreate":
        if (
            self.status == DocumentStatus.needs_resubmission
            and not self.resubmission_reason
        ):
            raise ValueError(
                "resubmission_reason is required when status is 'needs_resubmission'."
            )
        return self


class DocumentRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    requirement_id: uuid.UUID | None
    # Surface the requirement short-code alongside the FK so the frontend
    # checklist/doc-table doesn't need a separate requirements lookup per
    # row. Populated by the service layer when requirement_id is present.
    requirement_code: str | None = None
    document_type: str
    current_version: int
    current_status: DocumentStatus
    resubmission_reason: str | None
    created_at: datetime
    updated_at: datetime
    latest_version: DocumentVersionRead | None = None
