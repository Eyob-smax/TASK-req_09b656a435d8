from enum import Enum


class UserRole(str, Enum):
    candidate = "candidate"
    proctor = "proctor"
    reviewer = "reviewer"
    admin = "admin"


class OrderStatus(str, Enum):
    pending_payment = "pending_payment"
    pending_fulfillment = "pending_fulfillment"
    pending_receipt = "pending_receipt"
    completed = "completed"
    canceled = "canceled"
    refund_in_progress = "refund_in_progress"
    refunded = "refunded"


class DocumentStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    needs_resubmission = "needs_resubmission"


class BargainingStatus(str, Enum):
    open = "open"
    accepted = "accepted"
    countered = "countered"
    counter_accepted = "counter_accepted"
    expired = "expired"
    rejected = "rejected"


class BargainingOfferOutcome(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    countered = "countered"
    expired = "expired"


class ExceptionStatus(str, Enum):
    pending_proof = "pending_proof"
    pending_initial_review = "pending_initial_review"
    pending_final_review = "pending_final_review"
    approved = "approved"
    rejected = "rejected"


class ReviewStage(str, Enum):
    initial = "initial"
    final = "final"


class ReviewDecision(str, Enum):
    approve = "approve"
    reject = "reject"
    escalate = "escalate"


class PricingMode(str, Enum):
    fixed = "fixed"
    bargaining = "bargaining"


class AnomalyType(str, Enum):
    absent = "absent"
    missed_checkin = "missed_checkin"
    late_arrival = "late_arrival"
    early_departure = "early_departure"
    other = "other"


class AuditEventType(str, Enum):
    login_success = "login_success"
    login_failure = "login_failure"
    logout = "logout"
    document_uploaded = "document_uploaded"
    document_downloaded = "document_downloaded"
    document_reviewed = "document_reviewed"
    order_created = "order_created"
    order_state_changed = "order_state_changed"
    bargaining_offer_submitted = "bargaining_offer_submitted"
    bargaining_resolved = "bargaining_resolved"
    exception_created = "exception_created"
    exception_reviewed = "exception_reviewed"
    exception_approved = "exception_approved"
    feature_flag_changed = "feature_flag_changed"
    cohort_assigned = "cohort_assigned"
    export_generated = "export_generated"
    sensitive_field_accessed = "sensitive_field_accessed"
    password_changed = "password_changed"
    device_registered = "device_registered"
    device_revoked = "device_revoked"
