"""
Security-domain exceptions.

These exceptions are raised by primitives in `src/security/*` and caught by
the FastAPI exception handlers in `src/api/errors.py`, which render them into
the shared error envelope defined in `src/schemas/common.py`.
"""
from __future__ import annotations


class SecurityError(Exception):
    """Base for every security-layer exception."""

    code: str = "SECURITY_ERROR"
    http_status: int = 400

    def __init__(self, message: str = "", *, details: list[dict] | None = None):
        super().__init__(message or self.code)
        self.message = message or self.code
        self.details = details or []


class AuthError(SecurityError):
    code = "AUTH_REQUIRED"
    http_status = 401


class TokenExpiredError(AuthError):
    code = "TOKEN_EXPIRED"


class TokenInvalidError(AuthError):
    code = "AUTH_REQUIRED"


class ThrottledError(SecurityError):
    code = "AUTH_THROTTLED"
    http_status = 429


class NonceReplayError(SecurityError):
    code = "NONCE_REPLAY"
    http_status = 409


class ClockSkewError(SecurityError):
    code = "CLOCK_SKEW"
    http_status = 400


class SignatureInvalidError(SecurityError):
    code = "SIGNATURE_INVALID"
    http_status = 400


class ForbiddenError(SecurityError):
    code = "FORBIDDEN"
    http_status = 403


class OwnershipError(ForbiddenError):
    code = "FORBIDDEN"


class DeviceNotFoundError(SecurityError):
    code = "DEVICE_NOT_FOUND"
    http_status = 404


class EncryptionError(SecurityError):
    code = "ENCRYPTION_ERROR"
    http_status = 500


class DecryptionError(SecurityError):
    code = "DECRYPTION_ERROR"
    http_status = 500


class IdempotencyConflictError(SecurityError):
    code = "IDEMPOTENCY_CONFLICT"
    http_status = 409


class BusinessRuleError(SecurityError):
    code = "BUSINESS_RULE_VIOLATION"
    http_status = 409


class ResourceNotFoundError(SecurityError):
    code = "NOT_FOUND"
    http_status = 404


class PolicyViolationError(SecurityError):
    code = "POLICY_VIOLATION"
    http_status = 422
