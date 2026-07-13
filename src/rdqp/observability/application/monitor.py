"""Small in-process health and metrics registry."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from time import perf_counter

from rdqp.observability.domain.models import ComponentHealth, HealthStatus, RuntimeMetric


class HealthMonitor:
    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], tuple[HealthStatus, str]]] = {}

    def register(self, name: str, check: Callable[[], tuple[HealthStatus, str]]) -> None:
        if not name.strip():
            raise ValueError("health check name must not be empty")
        self._checks[name] = check

    def run(self) -> tuple[ComponentHealth, ...]:
        results: list[ComponentHealth] = []
        for name, check in self._checks.items():
            started = perf_counter()
            try:
                status, message = check()
            except Exception as exc:  # defensive boundary around infrastructure checks
                status, message = HealthStatus.UNHEALTHY, str(exc)
            latency = (perf_counter() - started) * 1000
            results.append(
                ComponentHealth(name, status, message, datetime.now(timezone.utc), latency)
            )
        return tuple(results)


class MetricsRegistry:
    def __init__(self) -> None:
        self._values: dict[str, RuntimeMetric] = {}

    def set(self, name: str, value: float, unit: str = "count") -> None:
        self._values[name] = RuntimeMetric(name, float(value), unit, datetime.now(timezone.utc))

    def increment(self, name: str, amount: float = 1.0, unit: str = "count") -> None:
        current = self._values.get(name)
        self.set(name, (current.value if current else 0.0) + amount, unit)

    def snapshot(self) -> tuple[RuntimeMetric, ...]:
        return tuple(sorted(self._values.values(), key=lambda metric: metric.name))
