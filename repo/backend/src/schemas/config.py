import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FeatureFlagRead(BaseModel):
    id: uuid.UUID
    key: str
    value: str
    value_type: str
    description: str | None
    updated_by: uuid.UUID | None
    updated_at: datetime


class FeatureFlagUpdate(BaseModel):
    value: str = Field(..., min_length=1)
    change_reason: str | None = Field(None, max_length=500)


class CohortDefinitionRead(BaseModel):
    id: uuid.UUID
    cohort_key: str
    name: str
    description: str | None
    flag_overrides: dict | None
    is_active: bool
    created_at: datetime


class CohortDefinitionCreate(BaseModel):
    cohort_key: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    flag_overrides: dict | None = None


class CohortAssignmentCreate(BaseModel):
    user_id: uuid.UUID


class BootstrapConfigResponse(BaseModel):
    user_id: uuid.UUID
    role: str
    cohort_key: str | None
    feature_flags: dict[str, str]
    flag_overrides: dict[str, str]
    resolved_flags: dict[str, str]
    issued_at: datetime
    signature: str
