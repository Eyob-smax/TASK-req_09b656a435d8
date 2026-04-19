"""
Verifies the Settings schema parses valid defaults and rejects invalid input.
No network or filesystem I/O.
"""
import pytest


def test_config_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@localhost/db")
    monkeypatch.setenv("SECRET_KEY", "s" * 32)
    monkeypatch.setenv("ENVIRONMENT", "development")

    from src.config import Settings
    s = Settings()  # type: ignore[call-arg]

    assert s.access_token_expire_minutes == 15
    assert s.max_upload_size_bytes == 25 * 1024 * 1024
    assert s.nonce_window_seconds == 300
    assert s.auto_cancel_minutes == 30
    assert s.after_sales_window_days == 14
    assert s.max_bargaining_offers == 3
    assert "application/pdf" in s.allowed_mime_types
    assert "image/jpeg" in s.allowed_mime_types
    assert "image/png" in s.allowed_mime_types


def test_config_missing_database_url_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "s" * 32)

    from pydantic import ValidationError
    from src.config import Settings
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_config_short_secret_key_raises(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@localhost/db")
    monkeypatch.setenv("SECRET_KEY", "tooshort")

    from pydantic import ValidationError
    from src.config import Settings
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_config_invalid_environment_raises(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@localhost/db")
    monkeypatch.setenv("SECRET_KEY", "s" * 32)
    monkeypatch.setenv("ENVIRONMENT", "staging")

    from pydantic import ValidationError
    from src.config import Settings
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]
