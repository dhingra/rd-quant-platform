"""Notification routing with deduplication and cooldowns."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol

from rdqp.notifications.domain.models import Notification


class NotificationSink(Protocol):
    def send(self, notification: Notification) -> None: ...


class NotificationRouter:
    def __init__(self, sinks: list[NotificationSink] | None = None, cooldown_seconds: int = 60) -> None:
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")
        self._sinks = list(sinks or [])
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._last_sent: dict[str, datetime] = {}

    def add_sink(self, sink: NotificationSink) -> None:
        self._sinks.append(sink)

    def publish(self, notification: Notification, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        key = notification.dedupe_key or f"{notification.category}:{notification.symbol}:{notification.title}"
        previous = self._last_sent.get(key)
        if previous is not None and now - previous < self._cooldown:
            return False
        for sink in self._sinks:
            sink.send(notification)
        self._last_sent[key] = now
        return True
