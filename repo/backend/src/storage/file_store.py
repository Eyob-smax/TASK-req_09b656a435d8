"""
Local filesystem storage for uploaded documents and exception proofs.

Layout:
  documents : {root}/{candidate_id}/{document_id}/v{version}/{filename}
  exceptions: {root}/exceptions/{exception_id}/{doc_version_id}/{filename}

SHA-256 is computed synchronously at upload time (before async write) so the
hash is captured before any I/O failure can corrupt the record.
"""
from __future__ import annotations

import asyncio
import hashlib
import uuid
from pathlib import Path

from ..config import get_settings


class FileStore:
    def __init__(self, root: str) -> None:
        self._root = Path(root)

    # ── Document uploads ─────────────────────────────────────────────────────

    async def write_document(
        self,
        candidate_id: uuid.UUID,
        document_id: uuid.UUID,
        version: int,
        filename: str,
        data: bytes,
    ) -> str:
        dir_path = self._root / str(candidate_id) / str(document_id) / f"v{version}"
        await asyncio.to_thread(dir_path.mkdir, parents=True, exist_ok=True)
        file_path = dir_path / filename
        await asyncio.to_thread(file_path.write_bytes, data)
        return str(file_path)

    # ── Exception proofs ─────────────────────────────────────────────────────

    async def write_proof(
        self,
        exception_id: uuid.UUID,
        doc_version_id: uuid.UUID,
        filename: str,
        data: bytes,
    ) -> str:
        dir_path = self._root / "exceptions" / str(exception_id) / str(doc_version_id)
        await asyncio.to_thread(dir_path.mkdir, parents=True, exist_ok=True)
        file_path = dir_path / filename
        await asyncio.to_thread(file_path.write_bytes, data)
        return str(file_path)

    # ── Generic read / delete ─────────────────────────────────────────────────

    async def read(self, stored_path: str) -> bytes:
        path = Path(stored_path)
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, stored_path: str) -> None:
        path = Path(stored_path)
        await asyncio.to_thread(path.unlink, True)

    # ── Hash ─────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


_file_store: FileStore | None = None


def get_file_store() -> FileStore:
    global _file_store
    if _file_store is None:
        settings = get_settings()
        _file_store = FileStore(settings.storage_root)
    return _file_store


def install_file_store(store: FileStore) -> None:
    """Override for tests."""
    global _file_store
    _file_store = store
