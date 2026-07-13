"""Persistent scheduler state storage."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteAutomationStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def set(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO automation_state(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, payload),
            )

    def get(self, key: str, default: Any = None) -> Any:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM automation_state WHERE key=?", (key,)).fetchone()
        return default if row is None else json.loads(row[0])

    def delete(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM automation_state WHERE key=?", (key,))

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)
