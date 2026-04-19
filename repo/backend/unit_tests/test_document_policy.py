import pytest

from src.domain.document_policy import (
    MAX_SIZE_BYTES,
    DocumentPolicyViolation,
    validate_review_decision,
    validate_upload,
    requires_resubmission_reason,
)
from src.domain.enums import DocumentStatus


class TestValidateUpload:
    def test_pdf_accepted(self):
        validate_upload("application/pdf", 1024)

    def test_jpeg_accepted(self):
        validate_upload("image/jpeg", 1024)

    def test_png_accepted(self):
        validate_upload("image/png", 1024)

    def test_exactly_25mb_accepted(self):
        validate_upload("application/pdf", MAX_SIZE_BYTES)

    def test_over_25mb_rejected(self):
        with pytest.raises(DocumentPolicyViolation) as exc_info:
            validate_upload("application/pdf", MAX_SIZE_BYTES + 1)
        assert exc_info.value.code == "FILE_TOO_LARGE"

    def test_disallowed_mime_type_rejected(self):
        with pytest.raises(DocumentPolicyViolation) as exc_info:
            validate_upload("application/zip", 1024)
        assert exc_info.value.code == "FILE_TYPE_NOT_ALLOWED"

    def test_word_doc_rejected(self):
        with pytest.raises(DocumentPolicyViolation) as exc_info:
            validate_upload("application/msword", 1024)
        assert exc_info.value.code == "FILE_TYPE_NOT_ALLOWED"

    def test_gif_rejected(self):
        with pytest.raises(DocumentPolicyViolation) as exc_info:
            validate_upload("image/gif", 1024)
        assert exc_info.value.code == "FILE_TYPE_NOT_ALLOWED"

    def test_zero_size_pdf_accepted(self):
        validate_upload("application/pdf", 0)


class TestRequiresResubmissionReason:
    def test_needs_resubmission_requires_reason(self):
        assert requires_resubmission_reason(DocumentStatus.needs_resubmission) is True

    def test_approved_does_not_require_reason(self):
        assert requires_resubmission_reason(DocumentStatus.approved) is False

    def test_rejected_does_not_require_reason(self):
        assert requires_resubmission_reason(DocumentStatus.rejected) is False

    def test_pending_review_does_not_require_reason(self):
        assert requires_resubmission_reason(DocumentStatus.pending_review) is False


class TestValidateReviewDecision:
    def test_needs_resubmission_with_reason_passes(self):
        validate_review_decision(DocumentStatus.needs_resubmission, "Missing notarization.")

    def test_needs_resubmission_without_reason_raises(self):
        with pytest.raises(DocumentPolicyViolation) as exc_info:
            validate_review_decision(DocumentStatus.needs_resubmission, None)
        assert exc_info.value.code == "RESUBMISSION_REASON_REQUIRED"

    def test_needs_resubmission_with_empty_reason_raises(self):
        with pytest.raises(DocumentPolicyViolation):
            validate_review_decision(DocumentStatus.needs_resubmission, "")

    def test_approved_without_reason_passes(self):
        validate_review_decision(DocumentStatus.approved, None)

    def test_rejected_without_reason_passes(self):
        validate_review_decision(DocumentStatus.rejected, None)
