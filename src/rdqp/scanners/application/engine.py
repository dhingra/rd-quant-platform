"""High-performance, side-effect-free scanner engine."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.scanners.domain.models import (
    FilterOperator,
    ScanDefinition,
    ScanMatch,
    ScanResult,
    ScannerFilter,
)


class ScannerEngine:
    """Evaluate composable filters over the latest cross-sectional factor snapshots."""

    _ALIASES = {"orb": "opening_range_state"}

    def run(self, definition: ScanDefinition, snapshots: list[FactorSnapshot]) -> ScanResult:
        started = perf_counter()
        rows = [self._to_row(item) for item in snapshots]
        matches = [row for row in rows if all(self._matches(row, f) for f in definition.filters)]
        matches.sort(
            key=lambda row: self._sort_value(row.get(definition.sort_by)),
            reverse=definition.descending,
        )
        limited = matches[: max(1, definition.limit)]
        elapsed_ms = (perf_counter() - started) * 1000
        return ScanResult(
            definition=definition,
            matches=tuple(
                ScanMatch(symbol=str(row["symbol"]), timestamp=row["timestamp"], values=row)
                for row in limited
            ),
            evaluated_count=len(rows),
            elapsed_ms=elapsed_ms,
            generated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def _to_row(cls, snapshot: FactorSnapshot) -> dict[str, Any]:
        row = asdict(snapshot)
        row["roc_pct"] = None if snapshot.roc is None else snapshot.roc * 100
        row["gap_pct"] = None if snapshot.gap is None else snapshot.gap * 100
        row["vwap_distance_pct"] = (
            None if snapshot.vwap_distance is None else snapshot.vwap_distance * 100
        )
        row["above_vwap"] = bool(snapshot.vwap is not None and snapshot.price > snapshot.vwap)
        row["below_vwap"] = bool(snapshot.vwap is not None and snapshot.price < snapshot.vwap)
        row["orb_breakout"] = snapshot.opening_range_state == "breakout"
        row["orb_breakdown"] = snapshot.opening_range_state == "breakdown"
        return row

    @classmethod
    def _sort_value(cls, value: Any) -> tuple[int, Any]:
        return (0, 0) if value is None else (1, value)

    @classmethod
    def _matches(cls, row: dict[str, Any], filter_: ScannerFilter) -> bool:
        field = cls._ALIASES.get(filter_.field, filter_.field)
        left = row.get(field)
        op = filter_.operator
        right = filter_.value
        if op == FilterOperator.IS_TRUE:
            return bool(left)
        if op == FilterOperator.IS_FALSE:
            return not bool(left)
        if left is None:
            return False
        if op == FilterOperator.GT:
            return left > right
        if op == FilterOperator.GTE:
            return left >= right
        if op == FilterOperator.LT:
            return left < right
        if op == FilterOperator.LTE:
            return left <= right
        if op == FilterOperator.EQ:
            return left == right
        if op == FilterOperator.NE:
            return left != right
        if op == FilterOperator.IN:
            return left in right
        if op == FilterOperator.NOT_IN:
            return left not in right
        if op == FilterOperator.BETWEEN:
            return right <= left <= filter_.second_value
        if op == FilterOperator.CONTAINS:
            return str(right).lower() in str(left).lower()
        raise ValueError(f"Unsupported scanner operator: {op}")
