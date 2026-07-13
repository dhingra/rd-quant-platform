"""Built-in notification sinks."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rdqp.notifications.domain.models import Notification


class InMemoryNotificationSink:
    def __init__(self, max_items: int = 500) -> None:
        self.max_items = max_items
        self.items: list[Notification] = []

    def send(self, notification: Notification) -> None:
        self.items.insert(0, notification)
        del self.items[self.max_items :]


class JsonlNotificationSink:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, notification: Notification) -> None:
        payload = asdict(notification)
        payload["severity"] = notification.severity.value
        payload["created_at"] = notification.created_at.isoformat()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
