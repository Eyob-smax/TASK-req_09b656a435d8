"""
Background worker: access-log aggregation and cache-hit rate reporting.

Runs every 900 seconds (15 min). The primary pipeline reads the JSON-lines
access logs written by `AccessLogMiddleware` (one file per day under
`settings.access_log_root`) and bucket-aggregates records that fall inside
the window:
  - AccessLogSummary: total requests, latency p50/p95, error count per endpoint group
  - CacheHitStat: cache hits/misses for static asset groups

Cache-hit derivation is authoritative (not heuristic): a static-asset record
is a HIT if status == 304 or `cache_status == "HIT"`, otherwise a MISS.

If `settings.cache_stats_log_backed` is False, or the access-log directory is
unreadable, or no records match the window, the worker falls back to the
legacy metrics-registry heuristic (fast 2xx static as hit) and emits a
`cache_stats_using_heuristic_fallback` warning.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import structlog

from ..config import get_settings
from ..persistence.repositories.config_repo import ConfigRepository
from ..telemetry.metrics import registry

logger = structlog.get_logger("workers.cache_stats")

# Path prefixes that classify as static assets
_STATIC_PREFIXES = ("/assets/", "/favicon", "/icons/", "/fonts/")
_API_PREFIX = "/api/"


def _classify_route(route: str) -> str:
    if any(route.startswith(p) for p in _STATIC_PREFIXES) or route in ("/", ""):
        return "static"
    if route.startswith(_API_PREFIX):
        return "api"
    return "other"


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    values_sorted = sorted(values)
    target = max(0, math.ceil(len(values_sorted) * pct / 100.0) - 1)
    return values_sorted[target]


def parse_access_log_window(
    access_log_root: str, window_start: datetime, window_end: datetime
) -> dict:
    """
    Parse JSON-line access logs and aggregate records within [window_start, window_end].

    Returns a dict with per-group totals, error counts, latency samples, and cache hits.
    """
    root = Path(access_log_root)
    aggregates: dict[str, dict] = {
        "api": {"total": 0, "errors": 0, "durations": [], "hits": 0, "misses": 0},
        "static": {"total": 0, "errors": 0, "durations": [], "hits": 0, "misses": 0},
        "other": {"total": 0, "errors": 0, "durations": [], "hits": 0, "misses": 0},
    }
    if not root.exists() or not root.is_dir():
        return aggregates

    window_start_ts = window_start.timestamp()
    window_end_ts = window_end.timestamp()

    for entry in sorted(root.glob("access-*.log")):
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        # Skip files whose entire mtime range cannot overlap the window.
        # Log files grow; rotation is daily. An active file has mtime >= window_start.
        if mtime < window_start_ts - 86400:
            continue
        try:
            with open(entry, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts_raw = record.get("ts")
                    if not isinstance(ts_raw, str):
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_raw)
                    except ValueError:
                        continue
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    rec_ts = ts.timestamp()
                    if rec_ts < window_start_ts or rec_ts > window_end_ts:
                        continue
                    path = record.get("path", "")
                    status = record.get("status", 0)
                    duration_ms = record.get("duration_ms", 0)
                    cache_status = record.get("cache_status", "")
                    group = _classify_route(path)
                    bucket = aggregates[group]
                    bucket["total"] += 1
                    if isinstance(status, int) and 400 <= status < 600:
                        bucket["errors"] += 1
                    if isinstance(duration_ms, (int, float)):
                        bucket["durations"].append(float(duration_ms))
                    if group == "static":
                        if status == 304 or cache_status == "HIT":
                            bucket["hits"] += 1
                        elif 200 <= status < 300:
                            bucket["misses"] += 1
        except OSError:
            continue
    return aggregates


def _extract_heuristic_fallback() -> tuple[dict, dict, float | None, float | None]:
    """Legacy heuristic from the live metrics registry. Returns (totals, errors, p50, p95)."""
    from ..telemetry.metrics import Histogram

    with registry._lock:
        metrics_snapshot = dict(registry._metrics)
    dur_metric = metrics_snapshot.get("merittrack_request_duration_seconds")
    group_totals: dict[str, int] = {"static": 0, "api": 0, "other": 0}
    group_errors: dict[str, int] = {"static": 0, "api": 0, "other": 0}
    p50_ms: float | None = None
    p95_ms: float | None = None

    if dur_metric is None or not isinstance(dur_metric, Histogram):
        return group_totals, group_errors, p50_ms, p95_ms

    with dur_metric._lock:
        all_totals = sum(dur_metric._totals.values())
        aggregated: list[int] = [0] * len(dur_metric.buckets)
        for counts in dur_metric._counts.values():
            for i, c in enumerate(counts):
                aggregated[i] += c
        for label_key, total in dur_metric._totals.items():
            label_dict = dict(label_key)
            route = label_dict.get("route", "")
            status = label_dict.get("status", "200")
            group = _classify_route(route)
            group_totals[group] = group_totals.get(group, 0) + total
            if status.startswith(("4", "5")):
                group_errors[group] = group_errors.get(group, 0) + total

    def pct(p: float) -> float | None:
        if all_totals == 0:
            return None
        target = math.ceil(all_totals * p / 100.0)
        cumulative = 0
        for boundary, count in zip(dur_metric.buckets, aggregated):
            cumulative += count
            if cumulative >= target:
                return boundary * 1000
        return None

    p50_ms = pct(50)
    p95_ms = pct(95)
    return group_totals, group_errors, p50_ms, p95_ms


async def run_cache_stats_loop(session_factory, interval_seconds: int = 900) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        async with session_factory() as session:
            try:
                now = datetime.now(tz=timezone.utc)
                window_start = now - timedelta(seconds=interval_seconds)
                settings = get_settings()

                api_total = 0
                api_errors = 0
                static_total = 0
                static_errors = 0
                cache_hits = 0
                cache_misses = 0
                p50_ms: float | None = None
                p95_ms: float | None = None
                used_fallback = False
                fallback_reason = ""

                log_root = settings.access_log_root
                if not settings.cache_stats_log_backed:
                    used_fallback = True
                    fallback_reason = "log_backed_disabled"
                elif not os.path.isdir(log_root):
                    used_fallback = True
                    fallback_reason = "log_dir_missing"
                else:
                    aggregates = parse_access_log_window(log_root, window_start, now)
                    api_bucket = aggregates["api"]
                    static_bucket = aggregates["static"]
                    api_total = api_bucket["total"]
                    api_errors = api_bucket["errors"]
                    static_total = static_bucket["total"]
                    static_errors = static_bucket["errors"]
                    cache_hits = static_bucket["hits"]
                    cache_misses = static_bucket["misses"]
                    all_durations = (
                        api_bucket["durations"]
                        + static_bucket["durations"]
                        + aggregates["other"]["durations"]
                    )
                    p50_ms = _percentile(all_durations, 50)
                    p95_ms = _percentile(all_durations, 95)
                    if api_total == 0 and static_total == 0:
                        used_fallback = True
                        fallback_reason = "no_matching_records"

                if used_fallback:
                    logger.warning(
                        "cache_stats_using_heuristic_fallback", reason=fallback_reason
                    )
                    totals, errors, p50_ms, p95_ms = _extract_heuristic_fallback()
                    api_total = totals.get("api", 0)
                    api_errors = errors.get("api", 0)
                    static_total = totals.get("static", 0)
                    static_errors = errors.get("static", 0)
                    cache_hits = max(0, static_total - static_errors)
                    cache_misses = static_total - cache_hits

                repo = ConfigRepository(session)
                await repo.upsert_access_log_summary(
                    window_start=window_start,
                    window_end=now,
                    endpoint_group="api",
                    total_requests=api_total,
                    p50_latency_ms=int(p50_ms) if p50_ms is not None else None,
                    p95_latency_ms=int(p95_ms) if p95_ms is not None else None,
                    error_count=api_errors,
                    computed_at=now,
                )
                await repo.upsert_cache_stat(
                    window_start=window_start,
                    window_end=now,
                    asset_group="static",
                    total_requests=static_total,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                    computed_at=now,
                )

                await session.commit()
                logger.info(
                    "cache_stats_computed",
                    window_start=window_start.isoformat(),
                    api_requests=api_total,
                    static_requests=static_total,
                    cache_hits=cache_hits,
                    source="heuristic" if used_fallback else "access_log_files",
                )
            except Exception:
                await session.rollback()
                logger.exception("cache_stats_loop_error")
