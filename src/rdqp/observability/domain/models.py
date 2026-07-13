"""Health and runtime metric domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    name: str
    status: HealthStatus
    message: str
    checked_at: datetime
    latency_ms: float | None = None


@dataclass(frozen=True, slots=True)
class RuntimeMetric:
    name: str
    value: float
    unit: str
    recorded_at: datetime
