import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_serializer

from ..domain.enums import UserRole


def _mask_ssn(ssn: str | None) -> str | None:
    if ssn is None:
        return None
    digits = ssn.replace("-", "").replace(" ", "")
    return f"***-**-{digits[-4:]}" if len(digits) >= 4 else "***"


def _mask_dob(dob: str | None) -> str | None:
    if dob is None:
        return None
    parts = dob.split("-")
    if len(parts) == 3:
        return f"{parts[0]}-**-**"
    return "****-**-**"


def _mask_phone(phone: str | None) -> str | None:
    if phone is None:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    return f"***-***-{digits[-4:]}" if len(digits) >= 4 else "***"


def _mask_email(email: str | None) -> str | None:
    if email is None:
        return None
    at = email.find("@")
    if at < 1:
        return "***@***.***"
    local = email[:at]
    domain = email[at + 1:]
    tld_dot = domain.rfind(".")
    tld = domain[tld_dot:] if tld_dot >= 0 else ""
    return f"{local[0]}***@***.{tld.lstrip('.')}"


class CandidateProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    preferred_name: str | None
    application_year: int | None
    application_status: str
    program_code: str | None
    created_at: datetime
    updated_at: datetime

    # Masked by default; override for privileged roles
    ssn_display: str | None = None
    dob_display: str | None = None
    phone_display: str | None = None
    email_display: str | None = None


class CandidateProfileUpdate(BaseModel):
    preferred_name: str | None = Field(None, max_length=255)
    application_year: int | None = None
    program_code: str | None = Field(None, max_length=50)
    notes: str | None = None


class ExamScoreRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    subject_code: str
    subject_name: str
    score: str
    max_score: str | None
    exam_date: datetime | None
    recorded_by: uuid.UUID | None
    created_at: datetime


class ExamScoreCreate(BaseModel):
    subject_code: str = Field(..., max_length=50)
    subject_name: str = Field(..., max_length=255)
    score: str = Field(..., max_length=50)
    max_score: str | None = Field(None, max_length=50)
    exam_date: datetime | None = None


class TransferPreferenceRead(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    institution_name: str
    program_code: str | None
    priority_rank: int
    notes: str | None
    is_active: bool
    created_at: datetime


class TransferPreferenceCreate(BaseModel):
    institution_name: str = Field(..., max_length=255)
    program_code: str | None = Field(None, max_length=50)
    priority_rank: int = Field(1, ge=1)
    notes: str | None = None


class TransferPreferenceUpdate(BaseModel):
    institution_name: str | None = Field(None, max_length=255)
    program_code: str | None = Field(None, max_length=50)
    priority_rank: int | None = Field(None, ge=1)
    notes: str | None = None
    is_active: bool | None = None
