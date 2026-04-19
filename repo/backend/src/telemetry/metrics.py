"""
Minimal in-memory Prometheus-style metrics registry.

This module intentionally avoids a Prometheus client dependency so it can
run in constrained deployments. It supports counters and histograms with
labels and exposes a ``render_metrics()`` helper that emits the text
exposition format (``# HELP`` / ``# TYPE`` / ``metric_name{labels} value``).
"""
from __future__ import annotations

import math
import threading
from typing import Mapping

LabelTuple = tuple[tuple[str, str], ...]


def _freeze_labels(labels: Mapping[str, str] | None) -> LabelTuple:
    if not labels:
        return ()
    return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


def _render_labels(labels: LabelTuple) -> str:
    if not labels:
        return ""
    parts = []
    for k, v in labels:
        escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        parts.append(f'{k}="{escaped}"')
    return "{" + ",".join(parts) + "}"


class Counter:
    """Monotonic counter with label support."""

    def __init__(self, name: str, description: str, labelnames: tuple[str, ...] = ()) -> None:
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames)
        self._values: dict[LabelTuple, float] = {}
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        if amount < 0:
            raise ValueError("Counter increment must be non-negative")
        key = _freeze_labels(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + float(amount)

    def value(self, **labels: str) -> float:
        key = _freeze_labels(labels)
        with self._lock:
            return self._values.get(key, 0.0)

    def render(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} counter",
        ]
        with self._lock:
            items = list(self._values.items())
        for label_key, val in items:
            lines.append(f"{self.name}{_render_labels(label_key)} {val}")
        return lines


class Histogram:
    """Histogram with configurable bucket boundaries."""

    DEFAULT_BUCKETS = (
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5,
        1.0, 2.5, 5.0, 10.0, math.inf,
    )

    def __init__(
        self,
        name: str,
        description: str,
        labelnames: tuple[str, ...] = (),
        buckets: tuple[float, ...] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.labelnames = tuple(labelnames)
        raw = tuple(buckets) if buckets else self.DEFAULT_BUCKETS
        if math.inf not in raw:
            raw = raw + (math.inf,)
        self.buckets = tuple(sorted(raw))
        self._counts: dict[LabelTuple, list[int]] = {}
        self._sums: dict[LabelTuple, float] = {}
        self._totals: dict[LabelTuple, int] = {}
        self._lock = threading.Lock()

    def observe(self, value: float, **labels: str) -> None:
        key = _freeze_labels(labels)
        with self._lock:
            counts = self._counts.setdefault(key, [0] * len(self.buckets))
            for i, boundary in enumerate(self.buckets):
                if value <= boundary:
                    counts[i] += 1
            self._sums[key] = self._sums.get(key, 0.0) + float(value)
            self._totals[key] = self._totals.get(key, 0) + 1

    def render(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram",
        ]
        with self._lock:
            keys = list(self._counts.keys())
            for key in keys:
                counts = self._counts[key]
                for boundary, count in zip(self.buckets, counts):
                    label_dict = dict(key)
                    label_dict["le"] = "+Inf" if boundary == math.inf else repr(boundary)
                    frozen = _freeze_labels(label_dict)
                    lines.append(f"{self.name}_bucket{_render_labels(frozen)} {count}")
                lines.append(
                    f"{self.name}_sum{_render_labels(key)} {self._sums.get(key, 0.0)}"
                )
                lines.append(
                    f"{self.name}_count{_render_labels(key)} {self._totals.get(key, 0)}"
                )
        return lines


class MetricsRegistry:
    """Process-wide registry. Not global state — held by module-level ``registry``."""

    def __init__(self) -> None:
        self._metrics: dict[str, Counter | Histogram] = {}
        self._lock = threading.Lock()

    def register(self, metric: Counter | Histogram) -> Counter | Histogram:
        with self._lock:
            if metric.name in self._metrics:
                return self._metrics[metric.name]
            self._metrics[metric.name] = metric
            return metric

    def counter(
        self, name: str, description: str, labelnames: tuple[str, ...] = ()
    ) -> Counter:
        with self._lock:
            existing = self._metrics.get(name)
            if existing is not None:
                if not isinstance(existing, Counter):
                    raise ValueError(f"{name} already registered as {type(existing).__name__}")
                return existing
            c = Counter(name, description, labelnames)
            self._metrics[name] = c
            return c

    def histogram(
        self,
        name: str,
        description: str,
        labelnames: tuple[str, ...] = (),
        buckets: tuple[float, ...] | None = None,
    ) -> Histogram:
        with self._lock:
            existing = self._metrics.get(name)
            if existing is not None:
                if not isinstance(existing, Histogram):
                    raise ValueError(f"{name} already registered as {type(existing).__name__}")
                return existing
            h = Histogram(name, description, labelnames, buckets)
            self._metrics[name] = h
            return h

    def render(self) -> str:
        with self._lock:
            metrics = list(self._metrics.values())
        lines: list[str] = []
        for metric in metrics:
            lines.extend(metric.render())
        return "\n".join(lines) + ("\n" if lines else "")

    def reset(self) -> None:
        """Test helper — clears every metric's state."""
        with self._lock:
            self._metrics.clear()


registry = MetricsRegistry()


login_attempts_total = registry.counter(
    "merittrack_login_attempts_total",
    "Total login attempts by outcome.",
    labelnames=("outcome",),
)

signature_failures_total = registry.counter(
    "merittrack_signature_failures_total",
    "Total rejected signed requests.",
    labelnames=("reason",),
)

request_duration_seconds = registry.histogram(
    "merittrack_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("route", "method", "status"),
)


document_uploads_total = registry.counter(
    "merittrack_document_uploads_total",
    "Total document upload attempts by outcome.",
    labelnames=("outcome",),
)

order_transitions_total = registry.counter(
    "merittrack_order_transitions_total",
    "Total order state transitions.",
    labelnames=("from_state", "to_state"),
)

exception_approvals_total = registry.counter(
    "merittrack_exception_approvals_total",
    "Total attendance exception review decisions.",
    labelnames=("outcome", "stage"),
)

queue_actions_total = registry.counter(
    "merittrack_queue_actions_total",
    "Total staff queue actions.",
    labelnames=("queue", "action"),
)

export_jobs_total = registry.counter(
    "merittrack_export_jobs_total",
    "Total export job completions.",
    labelnames=("export_type", "outcome"),
)

feature_flag_changes_total = registry.counter(
    "merittrack_feature_flag_changes_total",
    "Total feature flag change events.",
    labelnames=("key",),
)


def render_metrics() -> str:
    return registry.render()
