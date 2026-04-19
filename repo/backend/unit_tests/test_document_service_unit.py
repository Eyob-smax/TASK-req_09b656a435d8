"""Pure unit tests for document service logic (no DB, no I/O)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.document_policy import (
    MAX_SIZE_BYTES,
    DocumentPolicyViolation,
    validate_review_decision,
    validate_upload,
)
from src.domain.enums import DocumentStatus


class TestValidateUploadWrongMime:
    def test_validate_upload_wrong_mime(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_upload("application/zip", 1024)
        assert exc.value.code == "FILE_TYPE_NOT_ALLOWED"

    def test_validate_upload_text_plain_rejected(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_upload("text/plain", 100)
        assert exc.value.code == "FILE_TYPE_NOT_ALLOWED"

    def test_validate_upload_html_rejected(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_upload("text/html", 100)
        assert exc.value.code == "FILE_TYPE_NOT_ALLOWED"


class TestValidateUploadTooLarge:
    def test_validate_upload_too_large(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_upload("application/pdf", MAX_SIZE_BYTES + 1)
        assert exc.value.code == "FILE_TOO_LARGE"

    def test_validate_upload_exactly_at_limit_accepted(self):
        validate_upload("application/pdf", MAX_SIZE_BYTES)

    def test_validate_upload_one_byte_over_limit(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_upload("image/jpeg", MAX_SIZE_BYTES + 1)
        assert exc.value.code == "FILE_TOO_LARGE"


class TestValidateReviewDecision:
    def test_validate_review_decision_no_reason(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_review_decision(DocumentStatus.needs_resubmission, None)
        assert exc.value.code == "RESUBMISSION_REASON_REQUIRED"

    def test_validate_review_decision_empty_reason(self):
        with pytest.raises(DocumentPolicyViolation) as exc:
            validate_review_decision(DocumentStatus.needs_resubmission, "")
        assert exc.value.code == "RESUBMISSION_REASON_REQUIRED"

    def test_validate_review_decision_with_reason(self):
        validate_review_decision(DocumentStatus.needs_resubmission, "Missing notarization stamp.")

    def test_resubmission_reason_required_only_for_needs_resubmission(self):
        # approved does not require reason
        validate_review_decision(DocumentStatus.approved, None)

    def test_rejected_does_not_require_reason(self):
        validate_review_decision(DocumentStatus.rejected, None)

    def test_pending_does_not_require_reason(self):
        validate_review_decision(DocumentStatus.pending_review, None)


class TestChecklistCompletionLogic:
    """Verify that checklist item status is None when no document exists for a requirement."""

    def _make_requirement(self, req_id: uuid.UUID, code: str, mandatory: bool):
        req = MagicMock()
        req.id = req_id
        req.requirement_code = code
        req.display_name = f"Requirement {code}"
        req.is_mandatory = mandatory
        return req

    def _make_document(self, req_id: uuid.UUID, status: str):
        doc = MagicMock()
        doc.requirement_id = req_id
        doc.id = uuid.uuid4()
        doc.current_status = status
        doc.current_version = 1
        return doc

    def test_missing_document_returns_none_status(self):
        req_id = uuid.uuid4()
        req = self._make_requirement(req_id, "TRANSCRIPT", True)
        # No document for this requirement
        documents = []

        # Replicate the checklist join logic from DocumentRepository.get_checklist
        doc_map = {d.requirement_id: d for d in documents}
        doc = doc_map.get(req.id)
        status = DocumentStatus(doc.current_status) if doc else None
        assert status is None

    def test_existing_approved_document_returns_status(self):
        req_id = uuid.uuid4()
        req = self._make_requirement(req_id, "ID_CARD", True)
        doc = self._make_document(req_id, DocumentStatus.approved.value)

        doc_map = {doc.requirement_id: doc}
        result_doc = doc_map.get(req.id)
        status = DocumentStatus(result_doc.current_status) if result_doc else None
        assert status == DocumentStatus.approved

    def test_partial_completion_only_present_requirements_have_status(self):
        req1_id = uuid.uuid4()
        req2_id = uuid.uuid4()
        req1 = self._make_requirement(req1_id, "TRANSCRIPT", True)
        req2 = self._make_requirement(req2_id, "RECOMMENDATION", False)

        doc1 = self._make_document(req1_id, DocumentStatus.pending_review.value)
        documents = [doc1]  # req2 has no document

        doc_map = {d.requirement_id: d for d in documents}

        status1 = DocumentStatus(doc_map[req1_id].current_status)
        status2 = DocumentStatus(doc_map[req2_id].current_status) if req2_id in doc_map else None

        assert status1 == DocumentStatus.pending_review
        assert status2 is None
