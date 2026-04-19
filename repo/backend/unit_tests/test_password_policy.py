"""
Validates minimum-length password policy; no Argon2 cost exercised here.
"""
import pytest

from src.security.passwords import MIN_PASSWORD_LENGTH, PasswordPolicyError, validate_password_policy


def test_rejects_short_password():
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("short")


def test_rejects_boundary_minus_one():
    pwd = "a" * (MIN_PASSWORD_LENGTH - 1)
    with pytest.raises(PasswordPolicyError):
        validate_password_policy(pwd)


def test_accepts_exact_minimum():
    validate_password_policy("a" * MIN_PASSWORD_LENGTH)


def test_accepts_long_password():
    validate_password_policy("correct horse battery staple extra entropy")


def test_rejects_none():
    with pytest.raises(PasswordPolicyError):
        validate_password_policy(None)  # type: ignore[arg-type]


def test_unicode_width_counts_as_characters():
    # Counts by code-point length, not byte length
    pwd = "π" * 12
    validate_password_policy(pwd)
