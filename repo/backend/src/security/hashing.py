"""
SHA-256 helpers for uploads and downloads.
"""
from __future__ import annotations

import hashlib
from typing import IO

CHUNK = 65536


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_stream(stream: IO[bytes], chunk: int = CHUNK) -> str:
    h = hashlib.sha256()
    while True:
        buf = stream.read(chunk)
        if not buf:
            break
        h.update(buf)
    return h.hexdigest()


def verify_sha256_bytes(data: bytes, expected: str) -> bool:
    if not expected:
        return False
    return hashlib.sha256(data).hexdigest().lower() == expected.lower()


def verify_sha256_stream(stream: IO[bytes], expected: str) -> bool:
    if not expected:
        return False
    return sha256_of_stream(stream).lower() == expected.lower()
