"""
Centralized exception handlers.

Every handler converts its source exception into the shared error envelope
from `schemas.common`. No stack traces, no secret field values, no inner
messages that reveal account existence are returned. All detail is logged
via structlog instead.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..schemas.common import ErrorDetail, make_error
from ..security.errors import (
    AuthError,
    BusinessRuleError,
    ClockSkewError,
    DecryptionError,
    DeviceNotFoundError,
    EncryptionError,
    ForbiddenError,
    IdempotencyConflictError,
    NonceReplayError,
    PolicyViolationError,
    ResourceNotFoundError,
    SecurityError,
    SignatureInvalidError,
    ThrottledError,
    TokenExpiredError,
)
from ..telemetry.logging import get_logger

logger = get_logger("api.errors")


def _trace_id(request: Request) -> str | None:
    return getattr(request.state, "trace_id", None) or request.headers.get(
        "X-Request-ID"
    )


def _json(envelope, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(envelope.model_dump(mode="json")),
    )


async def _validation_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", ()) if p not in ("body",))
        details.append(
            ErrorDetail(field=loc or "body", message=err.get("msg", "Invalid value"))
        )
    logger.warning("validation_error", path=request.url.path, count=len(details))
    envelope = make_error(
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=details,
        trace_id=_trace_id(request),
    )
    return _json(envelope, status.HTTP_422_UNPROCESSABLE_ENTITY)


async def _security_handler(request: Request, exc: SecurityError):
    logger.warning(
        "security_error",
        code=exc.code,
        path=request.url.path,
        http_status=exc.http_status,
    )
    envelope = make_error(
        code=exc.code,
        message=exc.message,
        details=[ErrorDetail(**d) if isinstance(d, dict) else d for d in (exc.details or [])],
        trace_id=_trace_id(request),
    )
    return _json(envelope, exc.http_status)


async def _http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        code, message = "AUTH_REQUIRED", "Authentication required."
    elif exc.status_code == 403:
        code, message = "FORBIDDEN", "Access denied."
    elif exc.status_code == 404:
        code, message = "NOT_FOUND", "Resource not found."
    elif exc.status_code == 409:
        code, message = "CONFLICT", "Conflict."
    elif exc.status_code == 429:
        code, message = "RATE_LIMITED", "Rate limited."
    elif exc.status_code >= 500:
        code, message = "INTERNAL_ERROR", "An internal error occurred."
    else:
        code, message = "HTTP_ERROR", str(exc.detail) if exc.detail else "Request failed."
    logger.info("http_exception", code=code, path=request.url.path, http_status=exc.status_code)
    envelope = make_error(code=code, message=message, trace_id=_trace_id(request))
    return _json(envelope, exc.status_code)


async def _unhandled_handler(request: Request, exc: Exception):
    logger.exception(
        "internal_error",
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    )
    envelope = make_error(
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
        trace_id=_trace_id(request),
    )
    return _json(envelope, status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(TokenExpiredError, _security_handler)
    app.add_exception_handler(AuthError, _security_handler)
    app.add_exception_handler(ThrottledError, _security_handler)
    app.add_exception_handler(ForbiddenError, _security_handler)
    app.add_exception_handler(NonceReplayError, _security_handler)
    app.add_exception_handler(ClockSkewError, _security_handler)
    app.add_exception_handler(SignatureInvalidError, _security_handler)
    app.add_exception_handler(DeviceNotFoundError, _security_handler)
    app.add_exception_handler(IdempotencyConflictError, _security_handler)
    app.add_exception_handler(EncryptionError, _security_handler)
    app.add_exception_handler(DecryptionError, _security_handler)
    app.add_exception_handler(BusinessRuleError, _security_handler)
    app.add_exception_handler(ResourceNotFoundError, _security_handler)
    app.add_exception_handler(PolicyViolationError, _security_handler)
    app.add_exception_handler(SecurityError, _security_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
