from .enums import DocumentStatus

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"application/pdf", "image/jpeg", "image/png"}
)

MAX_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB


class DocumentPolicyViolation(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def validate_upload(mime_type: str, size_bytes: int) -> None:
    """Raise DocumentPolicyViolation if the file fails type or size checks."""
    if mime_type not in ALLOWED_MIME_TYPES:
        raise DocumentPolicyViolation(
            "FILE_TYPE_NOT_ALLOWED",
            f"File type '{mime_type}' is not accepted. Accepted: PDF, JPEG, PNG.",
        )
    if size_bytes > MAX_SIZE_BYTES:
        raise DocumentPolicyViolation(
            "FILE_TOO_LARGE",
            f"File size {size_bytes} bytes exceeds the 25 MB limit.",
        )


def requires_resubmission_reason(new_status: DocumentStatus) -> bool:
    """Return True when a resubmission reason must be supplied."""
    return new_status == DocumentStatus.needs_resubmission


def validate_review_decision(
    new_status: DocumentStatus,
    resubmission_reason: str | None,
) -> None:
    """Raise if a resubmission decision is missing its mandatory reason."""
    if requires_resubmission_reason(new_status) and not resubmission_reason:
        raise DocumentPolicyViolation(
            "RESUBMISSION_REASON_REQUIRED",
            "A reason must be provided when setting status to 'needs_resubmission'.",
        )
