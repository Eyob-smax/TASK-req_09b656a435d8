import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..domain.enums import UserRole


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=12, max_length=256)
    device_fingerprint: str | None = Field(None, max_length=128)
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: uuid.UUID
    role: UserRole
    cohort_config: dict | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class DeviceRegisterRequest(BaseModel):
    device_fingerprint: str = Field(..., min_length=8, max_length=128)
    public_key_pem: str = Field(..., min_length=1)
    label: str | None = Field(None, max_length=255)


class DeviceRegisterResponse(BaseModel):
    device_id: uuid.UUID
    device_fingerprint: str
    registered_at: datetime


class DeviceRead(BaseModel):
    device_id: uuid.UUID
    device_fingerprint: str
    label: str | None
    is_active: bool
    last_used_at: datetime | None
    registered_at: datetime


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=12, max_length=256)
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters.")
        return v


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    full_name: str
    is_active: bool
    last_login_at: datetime | None


class IdpTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str = "client_credentials"
    scope: str = ""


class IdpTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class DeviceChallengeRequest(BaseModel):
    device_fingerprint: str = Field(..., min_length=8, max_length=128)
    public_key_pem: str = Field(..., min_length=1)
    label: str | None = Field(None, max_length=255)


class DeviceChallengeResponse(BaseModel):
    challenge_id: str
    nonce: str
    expires_at: datetime


class DeviceActivateRequest(BaseModel):
    challenge_id: str
    device_fingerprint: str = Field(..., min_length=8, max_length=128)
    public_key_pem: str = Field(..., min_length=1)
    signature: str = Field(..., min_length=1)
    label: str | None = Field(None, max_length=255)


class DeviceRotateRequest(BaseModel):
    new_public_key_pem: str = Field(..., min_length=1)
    nonce: str = Field(..., min_length=1, max_length=64)
    timestamp: str = Field(...)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class MeResponse(BaseModel):
    user: UserRead
    cohort_config: dict | None = None
    device_id: uuid.UUID | None = None
    candidate_id: uuid.UUID | None = None
