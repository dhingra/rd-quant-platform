"""CSV persistence for normalized market ticks."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from rdqp.market.domain.models import Tick


class CsvTickStore:
    FIELDS = ("symbol", "timestamp", "price", "size", "source")

    def save(self, path: Path, ticks: list[Tick]) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDS)
            writer.writeheader()
            for tick in sorted(ticks, key=lambda item: (item.timestamp, item.symbol)):
                writer.writerow(
                    {
                        "symbol": tick.symbol,
                        "timestamp": tick.timestamp.isoformat(),
                        "price": tick.price,
                        "size": tick.size,
                        "source": tick.source,
                    }
                )
        return len(ticks)

    def load(self, path: Path) -> list[Tick]:
        if not path.exists():
            raise FileNotFoundError(path)
        ticks: list[Tick] = []
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                ticks.append(
                    Tick(
                        symbol=row["symbol"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        price=float(row["price"]),
                        size=float(row.get("size") or 0),
                        source=row.get("source") or "replay",
                    )
                )
        return ticks
