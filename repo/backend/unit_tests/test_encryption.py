"""
Envelope encryption: roundtrip, AAD binding, per-call IV uniqueness, rotation.
"""
import os

import pytest

from src.security import encryption
from src.security.errors import DecryptionError, EncryptionError


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://test:test@localhost/test")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)


@pytest.fixture(autouse=True)
def _install_key():
    encryption.install_kek("v1", os.urandom(32))
    yield
    encryption.clear_kek_overrides()


def test_encrypt_decrypt_roundtrip():
    payload, version = encryption.encrypt_field("secret-value")
    assert version == "v1"
    assert encryption.decrypt_field(payload) == "secret-value"


def test_ciphertexts_differ_per_call():
    c1, _ = encryption.encrypt_field("same")
    c2, _ = encryption.encrypt_field("same")
    assert c1 != c2
    assert encryption.decrypt_field(c1) == "same"
    assert encryption.decrypt_field(c2) == "same"


def test_wrong_aad_rejected():
    payload, _ = encryption.encrypt_field("secret", aad=b"resource:123")
    with pytest.raises(DecryptionError):
        encryption.decrypt_field(payload, aad=b"resource:other")


def test_wrong_version_pin_rejected():
    payload, _ = encryption.encrypt_field("secret")
    with pytest.raises(DecryptionError):
        encryption.decrypt_field(payload, key_version="v2")


def test_missing_version_prefix_rejected():
    with pytest.raises(DecryptionError):
        encryption.decrypt_field("no-separator-base64")


def test_corrupted_ciphertext_rejected():
    payload, _ = encryption.encrypt_field("secret")
    tampered = payload[:-4] + "ZZZZ"
    with pytest.raises(DecryptionError):
        encryption.decrypt_field(tampered)


def test_installed_bad_kek_rejected():
    with pytest.raises(EncryptionError):
        encryption.install_kek("v2", b"short")


def test_rotation_supported_for_legacy_payloads(monkeypatch):
    # Encrypt under v1
    old_payload, _ = encryption.encrypt_field("legacy")
    # Install v2 and make it current
    encryption.install_kek("v2", os.urandom(32))
    monkeypatch.setenv("KEK_CURRENT_VERSION", "v2")
    # v1 payload still decrypts because version prefix locates its KEK
    assert encryption.decrypt_field(old_payload) == "legacy"
