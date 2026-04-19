"""
Envelope encryption.

- KEK is a 32-byte AES-256 key loaded from `<kek_path>/<version>.key`.
- DEK is a fresh random 256-bit key per encryption call.
- Ciphertext is `AES-256-GCM(DEK, plaintext, aad)`.
- DEK is wrapped with KEK via a separate AES-256-GCM operation.
- On-disk format (base64-encoded):
    version_id|base64(wrap_iv|wrap_tag|wrapped_dek|data_iv|data_tag|ciphertext)
  Returned as (payload_string, key_version). `key_version` is also stored in a
  dedicated `*_key_version` column so rotation can re-wrap DEKs later without
  re-encrypting plaintext.
"""
from __future__ import annotations

import base64
import os
from functools import lru_cache

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..config import get_settings
from .errors import DecryptionError, EncryptionError

KEY_LENGTH = 32
IV_LENGTH = 12
TAG_LENGTH = 16
WRAPPED_DEK_LENGTH = KEY_LENGTH + TAG_LENGTH  # 48
VERSION_SEP = "|"

_KEK_OVERRIDE: dict[str, bytes] = {}


def install_kek(version: str, key: bytes) -> None:
    """Test/bootstrap hook: install a KEK in-memory without touching disk."""
    if len(key) != KEY_LENGTH:
        raise EncryptionError("KEK must be 32 bytes (AES-256).")
    _KEK_OVERRIDE[version] = key
    _load_kek.cache_clear()


def clear_kek_overrides() -> None:
    _KEK_OVERRIDE.clear()
    _load_kek.cache_clear()


@lru_cache(maxsize=8)
def _load_kek(version: str) -> bytes:
    if version in _KEK_OVERRIDE:
        return _KEK_OVERRIDE[version]
    settings = get_settings()
    path = os.path.join(settings.kek_path, f"{version}.key")
    with open(path, "rb") as f:
        key = f.read()
    if len(key) != KEY_LENGTH:
        raise EncryptionError(
            f"KEK file {path} is not 32 bytes."
        )
    return key


def _current_version() -> str:
    return get_settings().kek_current_version


def encrypt_field(plaintext: str, aad: bytes = b"") -> tuple[str, str]:
    """Return (payload_string, key_version)."""
    if plaintext is None:
        raise EncryptionError("Cannot encrypt None; caller must guard.")
    version = _current_version()
    kek = _load_kek(version)

    dek = AESGCM.generate_key(bit_length=256)
    data_iv = os.urandom(IV_LENGTH)
    wrap_iv = os.urandom(IV_LENGTH)

    dek_aead = AESGCM(dek)
    ct = dek_aead.encrypt(data_iv, plaintext.encode("utf-8"), aad)

    kek_aead = AESGCM(kek)
    wrapped = kek_aead.encrypt(wrap_iv, dek, None)

    blob = wrap_iv + wrapped + data_iv + ct
    payload = f"{version}{VERSION_SEP}{base64.b64encode(blob).decode('ascii')}"
    return payload, version


def decrypt_field(payload: str, key_version: str | None = None, aad: bytes = b"") -> str:
    if payload is None:
        raise DecryptionError("Cannot decrypt None.")
    if VERSION_SEP not in payload:
        raise DecryptionError("Ciphertext is missing the version prefix.")
    version, _, b64 = payload.partition(VERSION_SEP)
    if key_version is not None and key_version != version:
        raise DecryptionError("key_version does not match stored ciphertext version.")
    try:
        blob = base64.b64decode(b64, validate=True)
    except Exception as exc:
        raise DecryptionError("Ciphertext is not valid base64.") from exc
    try:
        wrap_iv = blob[:IV_LENGTH]
        wrapped = blob[IV_LENGTH : IV_LENGTH + WRAPPED_DEK_LENGTH]
        data_iv = blob[IV_LENGTH + WRAPPED_DEK_LENGTH : IV_LENGTH + WRAPPED_DEK_LENGTH + IV_LENGTH]
        ct = blob[IV_LENGTH + WRAPPED_DEK_LENGTH + IV_LENGTH :]
    except Exception as exc:
        raise DecryptionError("Ciphertext has the wrong structure.") from exc

    kek = _load_kek(version)
    try:
        dek = AESGCM(kek).decrypt(wrap_iv, wrapped, None)
    except InvalidTag as exc:
        raise DecryptionError("DEK unwrap failed; wrong KEK or tampered payload.") from exc
    try:
        pt = AESGCM(dek).decrypt(data_iv, ct, aad)
    except InvalidTag as exc:
        raise DecryptionError("Ciphertext decrypt failed; wrong AAD or tampered payload.") from exc
    return pt.decode("utf-8")
