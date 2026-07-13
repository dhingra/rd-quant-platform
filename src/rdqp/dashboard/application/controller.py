"""Application controller consumed by Streamlit; contains no UI imports."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from rdqp.analytics.application.factor_engine import ReactiveFactorEngine
from rdqp.analytics.application.market_analytics import market_statistics, sector_strength
from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.dashboard.application.sectors import sector_for
from rdqp.market.domain.models import Tick
from rdqp.scanners.application.alerts import AlertEngine
from rdqp.scanners.application.engine import ScannerEngine
from rdqp.scanners.domain.models import ScanDefinition, ScanResult, ScannerAlert


class DashboardController:
    def __init__(self, symbols: list[str], roc_window_seconds: int = 120, seed: int = 7) -> None:
        self.symbols = list(dict.fromkeys(s.upper() for s in symbols if s.strip()))
        self.engine = ReactiveFactorEngine(roc_window_seconds)
        self._random = random.Random(seed)
        self._prices = {s: self._random.uniform(30, 500) for s in self.symbols}
        self._clock = datetime.now(timezone.utc) - timedelta(seconds=roc_window_seconds + 30)
        self._seen: set[tuple[str, datetime]] = set()
        self.scanner = ScannerEngine()
        self.alerts = AlertEngine()

    def simulator_refresh(self, steps: int = 15) -> None:
        for _ in range(max(1, steps)):
            self._clock += timedelta(seconds=1)
            for symbol in self.symbols:
                price = max(0.01, self._prices[symbol] * (1 + self._random.gauss(0, 0.0015)))
                self._prices[symbol] = price
                self.engine.update(
                    Tick(
                        symbol, self._clock, price, self._random.randint(100, 20_000), "simulator"
                    ),
                    sector=sector_for(symbol),
                )

    def ingest(self, ticks: list[Tick]) -> None:
        for tick in sorted(ticks, key=lambda item: item.timestamp):
            key = (tick.symbol.upper(), tick.timestamp)
            if key in self._seen:
                continue
            self._seen.add(key)
            self.engine.update(tick, sector=sector_for(tick.symbol))

    def records(self) -> list[FactorSnapshot]:
        return self.engine.ranked()

    def statistics(self):
        return market_statistics(self.records())

    def sectors(self) -> list[dict[str, object]]:
        return sector_strength(self.records())

    def symbol_history(self, symbol: str) -> tuple[FactorSnapshot, ...]:
        return self.engine.history(symbol)

    def all_histories(self) -> dict[str, tuple[FactorSnapshot, ...]]:
        """Return immutable per-symbol history for backtesting and research consumers."""
        return {symbol: self.engine.history(symbol) for symbol in self.symbols}

    def run_scan(self, definition: ScanDefinition) -> ScanResult:
        return self.scanner.run(definition, self.records())

    def evaluate_alerts(self, result: ScanResult) -> tuple[ScannerAlert, ...]:
        return self.alerts.evaluate(result)
