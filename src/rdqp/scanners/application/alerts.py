"""Stateful alert generation for newly entering scanner matches."""

from __future__ import annotations

from datetime import datetime, timezone

from rdqp.scanners.domain.models import ScanResult, ScannerAlert


class AlertEngine:
    def __init__(self) -> None:
        self._previous: dict[str, set[str]] = {}

    def evaluate(self, result: ScanResult) -> tuple[ScannerAlert, ...]:
        current = {match.symbol for match in result.matches}
        previous = self._previous.get(result.definition.name, set())
        entered = sorted(current - previous)
        self._previous[result.definition.name] = current
        by_symbol = {match.symbol: match for match in result.matches}
        now = datetime.now(timezone.utc)
        return tuple(
            ScannerAlert(
                scan_name=result.definition.name,
                symbol=symbol,
                triggered_at=now,
                message=f"{symbol} entered scan '{result.definition.name}'",
                values=by_symbol[symbol].values,
            )
            for symbol in entered
        )

    def reset(self, scan_name: str | None = None) -> None:
        if scan_name is None:
            self._previous.clear()
        else:
            self._previous.pop(scan_name, None)
