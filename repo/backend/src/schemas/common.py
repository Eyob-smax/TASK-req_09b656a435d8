from datetime import datetime, timezone
from typing import Generic, TypeVar
import uuid

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    trace_id: str
    timestamp: datetime

    @classmethod
    def now(cls, trace_id: str | None = None) -> "ApiMeta":
        return cls(
            trace_id=trace_id or str(uuid.uuid4()),
            timestamp=datetime.now(tz=timezone.utc),
        )


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: ApiMeta


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody
    meta: ApiMeta


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: PaginationMeta
    meta: ApiMeta


def make_success(data: T, trace_id: str | None = None) -> SuccessResponse[T]:
    return SuccessResponse(data=data, meta=ApiMeta.now(trace_id))


def make_error(
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    trace_id: str | None = None,
) -> ErrorResponse:
    return ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details or []),
        meta=ApiMeta.now(trace_id),
    )
