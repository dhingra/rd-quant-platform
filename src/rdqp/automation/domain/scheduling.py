"""Automation scheduling and market-session policy models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo


class SessionDecision(StrEnum):
    ALLOWED = "ALLOWED"
    OUTSIDE_SESSION = "OUTSIDE_SESSION"
    WEEKEND = "WEEKEND"
    PAUSED = "PAUSED"


@dataclass(frozen=True, slots=True)
class MarketSessionPolicy:
    timezone_name: str = "America/New_York"
    start_time: time = time(9, 30)
    end_time: time = time(16, 0)
    weekdays_only: bool = True

    def evaluate(self, timestamp: datetime, paused: bool = False) -> SessionDecision:
        if paused:
            return SessionDecision.PAUSED
        local = timestamp.astimezone(ZoneInfo(self.timezone_name))
        if self.weekdays_only and local.weekday() >= 5:
            return SessionDecision.WEEKEND
        if not (self.start_time <= local.time().replace(tzinfo=None) <= self.end_time):
            return SessionDecision.OUTSIDE_SESSION
        return SessionDecision.ALLOWED


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    interval_seconds: int = 60
    max_consecutive_failures: int = 3
    session_policy: MarketSessionPolicy = MarketSessionPolicy()

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_consecutive_failures <= 0:
            raise ValueError("max_consecutive_failures must be positive")
