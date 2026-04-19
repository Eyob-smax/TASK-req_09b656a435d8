"""
HTTP middleware: trace ID injection + structured access logging + metrics.

In addition to emitting a structlog line per request, AccessLogMiddleware
appends a compact JSON record to a daily rotating file under
`settings.access_log_root`. The cache-stats worker reads these files to
compute window-level cache-hit / error / latency aggregates from the real
access log (not heuristic metric-registry inference).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..config import get_settings
from ..telemetry import metrics, tracing
from ..telemetry.logging import bind_trace_id, clear_trace_context, get_logger

logger = get_logger("api.access")

_STATIC_PREFIXES = ("/assets/", "/favicon", "/icons/", "/fonts/")
_LOG_DIR_READY: bool | None = None


def _ensure_log_dir(path: str) -> bool:
    """Create the access-log directory once per process; return readiness flag."""
    global _LOG_DIR_READY
    if _LOG_DIR_READY is not None:
        return _LOG_DIR_READY
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        _LOG_DIR_READY = True
    except OSError:
        logger.warning("access_log_dir_unavailable", path=path)
        _LOG_DIR_READY = False
    return _LOG_DIR_READY


def _classify_cache_status(path: str, status_code: int) -> str:
    """Classify a response as HIT / MISS / '' for access-log cache-hit derivation."""
    is_static = any(path.startswith(p) for p in _STATIC_PREFIXES) or path in ("/", "")
    if not is_static:
        return ""
    if status_code == 304:
        return "HIT"
    if 200 <= status_code < 300:
        return "MISS"
    return ""


class TraceIdMiddleware(BaseHTTPMiddleware):
    """
    Read or mint `X-Request-ID`; bind it into the structlog contextvar and
    echo it back on the response. Downstream handlers can read
    `request.state.trace_id`.
    """

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get(self.header_name) or tracing.new_trace_id()
        request.state.trace_id = trace_id
        bind_trace_id(trace_id)
        try:
            response = await call_next(request)
        finally:
            clear_trace_context()
        response.headers[self.header_name] = trace_id
        return response


class BodyBufferMiddleware(BaseHTTPMiddleware):
    """Buffer request body once and replay it for downstream consumers."""

    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        request.state.raw_body = body
        sent = False

        async def _receive() -> dict:
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        request._receive = _receive  # type: ignore[attr-defined]
        return await call_next(request)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Emit one structured log per request with method/path/status/duration.
    Records request duration into the shared Prometheus histogram and
    appends a JSON-line record to the daily access-log file so the
    cache-stats worker can aggregate from authoritative log data.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            route_template = request.url.path
            try:
                metrics.request_duration_seconds.observe(
                    duration,
                    route=route_template,
                    method=request.method,
                    status=str(status_code),
                )
            except Exception:
                pass
            duration_ms = int(duration * 1000)
            logger.info(
                "http_request",
                method=request.method,
                path=route_template,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            self._append_access_log_file(
                method=request.method,
                path=route_template,
                status_code=status_code,
                duration_ms=duration_ms,
            )

    @staticmethod
    def _append_access_log_file(
        *, method: str, path: str, status_code: int, duration_ms: int
    ) -> None:
        try:
            settings = get_settings()
            root = settings.access_log_root
            if not _ensure_log_dir(root):
                return
            now = datetime.now(tz=timezone.utc)
            filename = f"access-{now.strftime('%Y-%m-%d')}.log"
            record = {
                "ts": now.isoformat(),
                "method": method,
                "path": path,
                "status": status_code,
                "duration_ms": duration_ms,
                "cache_status": _classify_cache_status(path, status_code),
            }
            line = json.dumps(record, separators=(",", ":"))
            with open(os.path.join(root, filename), "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            # Never let access-log persistence failures break request handling.
            pass
