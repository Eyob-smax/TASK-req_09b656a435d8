"""
Argon2id password hashing and policy enforcement.

Policy: minimum 12 characters, no maximum imposed by policy (schema layer caps at 256).
Hashing parameters follow OWASP 2024 recommendations for Argon2id.
"""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions

MIN_PASSWORD_LENGTH = 12

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


class PasswordPolicyError(ValueError):
    """Raised when the plaintext password fails the policy check."""


def validate_password_policy(plain: str) -> None:
    if plain is None:
        raise PasswordPolicyError("Password is required.")
    if len(plain) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )


def hash_password(plain: str) -> str:
    validate_password_policy(plain)
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return _hasher.verify(hashed, plain)
    except argon2_exceptions.VerifyMismatchError:
        return False
    except argon2_exceptions.InvalidHashError:
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hashed)
    except argon2_exceptions.InvalidHashError:
        return True
