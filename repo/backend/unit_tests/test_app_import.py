"""
Verifies the FastAPI application module is importable and the app object is valid.
Does not start a server or require a database connection.
"""
import os
import pytest


@pytest.fixture(autouse=True)
def _patch_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://test:test@localhost/test")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("ENVIRONMENT", "development")


def test_app_importable():
    from src.main import app
    assert app is not None


def test_app_is_fastapi_instance():
    from fastapi import FastAPI
    from src.main import app
    assert isinstance(app, FastAPI)


def test_health_route_registered():
    from src.main import app
    routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
    assert "/api/v1/internal/health" in routes


def test_refund_progression_worker_registered():
    """Static check: refund progression worker is wired into lifespan task list."""
    import inspect

    from src import main as main_module

    src = inspect.getsource(main_module.lifespan)
    assert "run_refund_progression_loop" in src, (
        "refund progression worker must be started in lifespan"
    )
    assert hasattr(main_module, "run_refund_progression_loop"), (
        "refund progression worker symbol must be imported into main"
    )


def test_all_background_workers_registered():
    """All six background workers must be started in lifespan."""
    import inspect

    from src import main as main_module

    src = inspect.getsource(main_module.lifespan)
    expected_workers = [
        "run_auto_cancel_loop",
        "run_bargaining_expiry_loop",
        "run_stale_queue_loop",
        "run_cache_stats_loop",
        "run_forecasting_loop",
        "run_refund_progression_loop",
    ]
    for worker in expected_workers:
        assert worker in src, f"worker {worker} missing from lifespan"
