"""Notification domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class NotificationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class Notification:
    category: str
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    symbol: str | None = None
    dedupe_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
