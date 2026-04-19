from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.persistence.models.auth import User
from src.persistence.models.candidate import CandidateProfile
from src.persistence.models.order import ServiceItem
from src.security.passwords import hash_password


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be set for acceptance tests.")
    return value


def _acceptance_db_url() -> str:
    return _require_env("ACCEPTANCE_DATABASE_URL")


def _truncate_public_tables(db_engine) -> None:
    with db_engine.begin() as conn:
        table_names = conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public' AND tablename <> 'alembic_version'
                ORDER BY tablename
                """
            )
        ).scalars().all()
        if not table_names:
            return
        rendered = ", ".join(f'"{name}"' for name in table_names)
        conn.execute(text(f"TRUNCATE TABLE {rendered} RESTART IDENTITY CASCADE"))


@dataclass(frozen=True)
class DemoUser:
    user_id: uuid.UUID
    username: str
    password: str


@dataclass(frozen=True)
class SeedState:
    candidate: DemoUser
    reviewer: DemoUser
    admin: DemoUser
    proctor: DemoUser
    candidate_profile_id: uuid.UUID
    service_item_id: uuid.UUID


@pytest.fixture(scope="session")
def acceptance_base_url() -> str:
    return os.getenv("ACCEPTANCE_BASE_URL", "https://backend:8443").rstrip("/")


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(_acceptance_db_url(), future=True, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def seeded_state(db_engine) -> SeedState:
    _truncate_public_tables(db_engine)

    with Session(db_engine) as session:
        password = os.getenv("ACCEPTANCE_DEMO_PASSWORD", "MeritTrack!23456")
        users = {
            "candidate": User(
                username="demo_candidate",
                password_hash=hash_password(password),
                role="candidate",
                full_name="Demo Candidate",
                is_active=True,
                is_locked=False,
            ),
            "reviewer": User(
                username="demo_reviewer",
                password_hash=hash_password(password),
                role="reviewer",
                full_name="Demo Reviewer",
                is_active=True,
                is_locked=False,
            ),
            "admin": User(
                username="demo_admin",
                password_hash=hash_password(password),
                role="admin",
                full_name="Demo Admin",
                is_active=True,
                is_locked=False,
            ),
            "proctor": User(
                username="demo_proctor",
                password_hash=hash_password(password),
                role="proctor",
                full_name="Demo Proctor",
                is_active=True,
                is_locked=False,
            ),
        }
        session.add_all(list(users.values()))
        session.flush()

        profile = CandidateProfile(
            user_id=users["candidate"].id,
            preferred_name="Demo Candidate",
            application_year=2026,
            application_status="submitted",
            program_code="BSCS",
        )
        item = ServiceItem(
            item_code="SVC-ACCEPT-1",
            name="Acceptance Service",
            description="Seeded deterministic service for no-mock acceptance tests.",
            pricing_mode="bargaining",
            fixed_price=Decimal("1200.00"),
            bargaining_enabled=True,
            is_capacity_limited=False,
            is_active=True,
        )
        session.add_all([profile, item])
        session.commit()

        return SeedState(
            candidate=DemoUser(users["candidate"].id, users["candidate"].username, password),
            reviewer=DemoUser(users["reviewer"].id, users["reviewer"].username, password),
            admin=DemoUser(users["admin"].id, users["admin"].username, password),
            proctor=DemoUser(users["proctor"].id, users["proctor"].username, password),
            candidate_profile_id=profile.id,
            service_item_id=item.id,
        )


@pytest.fixture()
def http_client(acceptance_base_url: str):
    with httpx.Client(base_url=acceptance_base_url, verify=False, timeout=30.0) as client:
        yield client


def assert_success(resp: httpx.Response, expected_status: int = 200):
    assert resp.status_code == expected_status, resp.text
    body = resp.json()
    assert body.get("success") is True, body
    assert "meta" in body and body["meta"].get("trace_id"), body
    return body["data"]


def assert_error(resp: httpx.Response, expected_status: int):
    assert resp.status_code == expected_status, resp.text
    body = resp.json()
    assert body.get("success") is False, body
    assert body.get("error", {}).get("code"), body
    return body


def login(http_client: httpx.Client, username: str, password: str) -> dict:
    resp = http_client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": password,
            "nonce": f"n-{uuid.uuid4().hex}",
            "timestamp": _now_iso(),
        },
    )
    return assert_success(resp)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_device(http_client: httpx.Client, token: str, *, label: str) -> tuple[str, ec.EllipticCurvePrivateKey]:
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    resp = http_client.post(
        "/api/v1/auth/device/register",
        headers=bearer(token),
        json={
            "device_fingerprint": f"fp-{uuid.uuid4().hex[:16]}",
            "public_key_pem": pub_pem,
            "label": label,
        },
    )
    data = assert_success(resp)
    return data["device_id"], priv


def _make_signing_headers(
    private_key: ec.EllipticCurvePrivateKey,
    method: str,
    path: str,
    body_bytes: bytes,
    device_id: str,
) -> dict[str, str]:
    timestamp = _now_iso()
    nonce = f"n-{uuid.uuid4().hex}"
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    canonical = "\n".join([method.upper(), path, timestamp, nonce, device_id, body_hash]) + "\n"
    signature = base64.b64encode(
        private_key.sign(canonical.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    ).decode("utf-8")
    return {
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Device-ID": device_id,
        "X-Request-Signature": signature,
    }


def signed_post_json(
    http_client: httpx.Client,
    token: str,
    path: str,
    payload: dict,
    *,
    device: tuple[str, ec.EllipticCurvePrivateKey],
    extra_headers: dict[str, str] | None = None,
) -> httpx.Response:
    device_id, private_key = device
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        **bearer(token),
        "Content-Type": "application/json",
        **_make_signing_headers(private_key, "POST", path, body, device_id),
    }
    if extra_headers:
        headers.update(extra_headers)
    return http_client.post(path, content=body, headers=headers)


def _build_multipart(file_bytes: bytes, filename: str, content_type: str) -> tuple[bytes, str]:
    boundary = f"b-{uuid.uuid4().hex[:16]}"
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    body += file_bytes
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, f"multipart/form-data; boundary={boundary}"


def signed_post_multipart(
    http_client: httpx.Client,
    token: str,
    path: str,
    file_bytes: bytes,
    filename: str,
    *,
    content_type: str,
    device: tuple[str, ec.EllipticCurvePrivateKey],
) -> httpx.Response:
    device_id, private_key = device
    body, multipart_content_type = _build_multipart(file_bytes, filename, content_type)
    headers = {
        **bearer(token),
        "Content-Type": multipart_content_type,
        # Backend verifies multipart signatures against an empty body hash.
        **_make_signing_headers(private_key, "POST", path, b"", device_id),
    }
    return http_client.post(path, content=body, headers=headers)