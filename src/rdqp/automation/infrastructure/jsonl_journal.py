"""Append-only JSON Lines automation audit journal."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rdqp.automation.domain.models import AutomationRun


class JsonlAutomationJournal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, run: AutomationRun) -> None:
        payload = asdict(run)
        payload["mode"] = run.mode.value
        payload["started_at"] = run.started_at.isoformat()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")

    def recent(self, limit: int = 100) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:]][::-1]
