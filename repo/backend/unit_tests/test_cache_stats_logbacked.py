"""Unit tests for cache_stats log-backed parser and heuristic fallback."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest


def _write_access_log(tmp_path, filename: str, records: list[dict]) -> None:
    path = tmp_path / filename
    with open(path, "w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")


def test_cache_stats_parses_access_log_file(tmp_path):
    """Parser aggregates JSON-line access records into per-group totals and hits."""
    from src.workers.cache_stats import parse_access_log_window

    now = datetime.now(tz=timezone.utc)
    window_start = now - timedelta(minutes=15)
    in_window = (now - timedelta(minutes=5)).isoformat()
    out_of_window = (now - timedelta(hours=2)).isoformat()

    _write_access_log(
        tmp_path,
        f"access-{now.strftime('%Y-%m-%d')}.log",
        [
            {"ts": in_window, "method": "GET", "path": "/assets/app.js",
             "status": 200, "duration_ms": 3, "cache_status": "MISS"},
            {"ts": in_window, "method": "GET", "path": "/assets/app.js",
             "status": 304, "duration_ms": 1, "cache_status": "HIT"},
            {"ts": in_window, "method": "GET", "path": "/assets/app.js",
             "status": 200, "duration_ms": 2, "cache_status": "HIT"},
            {"ts": in_window, "method": "POST", "path": "/api/v1/orders",
             "status": 201, "duration_ms": 45, "cache_status": ""},
            {"ts": in_window, "method": "GET", "path": "/api/v1/orders/abc",
             "status": 500, "duration_ms": 120, "cache_status": ""},
            {"ts": in_window, "method": "GET", "path": "/api/v1/orders/abc",
             "status": 404, "duration_ms": 5, "cache_status": ""},
            # Out-of-window record: must be excluded.
            {"ts": out_of_window, "method": "GET", "path": "/assets/app.js",
             "status": 200, "duration_ms": 3, "cache_status": "MISS"},
        ],
    )

    result = parse_access_log_window(str(tmp_path), window_start, now)

    assert result["static"]["total"] == 3
    assert result["static"]["hits"] == 2
    assert result["static"]["misses"] == 1
    assert result["api"]["total"] == 3
    assert result["api"]["errors"] == 2


def test_cache_stats_parser_skips_malformed_records(tmp_path):
    """Malformed JSON lines, invalid timestamps, or non-JSON lines must not raise."""
    from src.workers.cache_stats import parse_access_log_window

    now = datetime.now(tz=timezone.utc)
    window_start = now - timedelta(minutes=15)
    good = (now - timedelta(minutes=3)).isoformat()

    path = tmp_path / f"access-{now.strftime('%Y-%m-%d')}.log"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("this is not json\n")
        fh.write(json.dumps({"ts": "not-a-date", "path": "/", "status": 200}) + "\n")
        fh.write(json.dumps({
            "ts": good, "method": "GET", "path": "/assets/a.js",
            "status": 304, "duration_ms": 1, "cache_status": "HIT",
        }) + "\n")

    result = parse_access_log_window(str(tmp_path), window_start, now)
    assert result["static"]["total"] == 1
    assert result["static"]["hits"] == 1


def test_cache_stats_returns_empty_when_dir_missing(tmp_path):
    """Missing access-log directory yields zeroed aggregates (caller triggers fallback)."""
    from src.workers.cache_stats import parse_access_log_window

    now = datetime.now(tz=timezone.utc)
    window_start = now - timedelta(minutes=15)
    missing = tmp_path / "does-not-exist"

    result = parse_access_log_window(str(missing), window_start, now)
    assert result["api"]["total"] == 0
    assert result["static"]["total"] == 0
    assert result["static"]["hits"] == 0


@pytest.mark.asyncio
async def test_cache_stats_falls_back_to_heuristic_on_missing_dir(tmp_path, monkeypatch):
    """When the log directory doesn't exist, worker uses registry heuristic + warns."""
    import asyncio

    import src.workers.cache_stats as cs_mod

    missing_path = str(tmp_path / "no-logs-here")

    class _StubSettings:
        access_log_root = missing_path
        cache_stats_log_backed = True

    monkeypatch.setattr(cs_mod, "get_settings", lambda: _StubSettings())

    calls: list[dict] = []

    class _StubRepo:
        def __init__(self, session):
            self.session = session

        async def upsert_access_log_summary(self, **kwargs):
            calls.append({"kind": "access_log", **kwargs})

        async def upsert_cache_stat(self, **kwargs):
            calls.append({"kind": "cache_stat", **kwargs})

    monkeypatch.setattr(cs_mod, "ConfigRepository", _StubRepo)

    class _Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

    def _factory():
        return _Session()

    warnings: list[tuple] = []

    class _StubLogger:
        def warning(self, event, **kwargs):
            warnings.append((event, kwargs))

        def info(self, *args, **kwargs):
            pass

        def exception(self, *args, **kwargs):
            pass

    monkeypatch.setattr(cs_mod, "logger", _StubLogger())

    task = asyncio.create_task(cs_mod.run_cache_stats_loop(_factory, interval_seconds=0.05))
    await asyncio.sleep(0.2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    kinds = {c["kind"] for c in calls}
    assert "access_log" in kinds
    assert "cache_stat" in kinds
    assert any(ev == "cache_stats_using_heuristic_fallback" for ev, _ in warnings)
