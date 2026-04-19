"""
Column-level masking helpers + privileged-role bypass.
"""
from src.domain.enums import UserRole
from src.security.data_masking import (
    SerializationContext,
    is_privileged,
    mask_dob,
    mask_email,
    mask_phone,
    mask_ssn,
)


def test_mask_ssn_keeps_last_four():
    assert mask_ssn("123-45-6789") == "***-**-6789"


def test_mask_ssn_handles_none():
    assert mask_ssn(None) is None


def test_mask_dob_year_only_string():
    assert mask_dob("1990-05-12") == "1990-**-**"


def test_mask_dob_year_only_datetime():
    from datetime import date

    assert mask_dob(date(2001, 1, 2)) == "2001-**-**"


def test_mask_phone_last_four():
    assert mask_phone("+1 (415) 555-0199") == "***-***-0199"


def test_mask_phone_short_value():
    assert mask_phone("1") == "***"


def test_mask_email_domain_only():
    assert mask_email("alice@example.com") == "***@example.com"


def test_mask_email_no_at_passthrough():
    assert mask_email("not-an-email") == "not-an-email"


def test_is_privileged_reviewer_admin_true():
    assert is_privileged(UserRole.reviewer) is True
    assert is_privileged(UserRole.admin) is True


def test_is_privileged_candidate_proctor_false():
    assert is_privileged(UserRole.candidate) is False
    assert is_privileged(UserRole.proctor) is False


def test_is_privileged_accepts_str():
    assert is_privileged("admin") is True
    assert is_privileged("candidate") is False


def test_is_privileged_none():
    assert is_privileged(None) is False


def test_serialization_context_privileged_flag():
    assert SerializationContext(actor_role=UserRole.admin).privileged is True
    assert SerializationContext(actor_role=UserRole.candidate).privileged is False
    assert SerializationContext().privileged is False
