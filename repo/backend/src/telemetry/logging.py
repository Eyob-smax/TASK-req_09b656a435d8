"""
Structured logging with a secret-safe processor.

All logs are JSON-serialized and pass through a redactor that strips known
sensitive keys before emission.
"""
from __future__ import annotations

import logging
from typing import Any

import structlog

SENSITIVE_KEYS = {
    "password",
    "current_password",
    "new_password",
    "password_hash",
    "refresh_token",
    "access_token",
    "token",
    "client_secret",
    "client_secret_hash",
    "public_key_pem",
    "private_key_pem",
    "signature",
    "x-request-signature",
    "authorization",
    "ssn",
    "dob",
    "date_of_birth",
}
REDACTED = "[REDACTED]"


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: (REDACTED if k.lower() in SENSITIVE_KEYS else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def redact_processor(logger, method_name, event_dict):  # noqa: ARG001
    for k in list(event_dict.keys()):
        if k.lower() in SENSITIVE_KEYS:
            event_dict[k] = REDACTED
        elif isinstance(event_dict[k], (dict, list)):
            event_dict[k] = _redact(event_dict[k])
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            redact_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name or "merittrack")


def bind_trace_id(trace_id: str) -> None:
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def clear_trace_context() -> None:
    structlog.contextvars.clear_contextvars()
