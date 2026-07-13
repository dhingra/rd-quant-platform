"""Incremental per-symbol factor and cross-sectional analytics engine."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import replace
from datetime import datetime, timedelta
from statistics import median

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.market.domain.models import Tick


class ReactiveFactorEngine:
    """Updates only the symbol affected by each incoming tick."""

    def __init__(self, roc_window_seconds: int = 120, opening_range_minutes: int = 30) -> None:
        if roc_window_seconds <= 0:
            raise ValueError("roc_window_seconds must be positive")
        self._roc_window = timedelta(seconds=roc_window_seconds)
        self._opening_range = timedelta(minutes=opening_range_minutes)
        self._prices: dict[str, deque[tuple[datetime, float]]] = defaultdict(deque)
        self._volumes: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=30))
        self._pv: dict[str, float] = defaultdict(float)
        self._volume_sum: dict[str, float] = defaultdict(float)
        self._session_date: dict[str, object] = {}
        self._session_start: dict[str, datetime] = {}
        self._open: dict[str, float] = {}
        self._previous_close: dict[str, float] = {}
        self._or_high: dict[str, float] = {}
        self._or_low: dict[str, float] = {}
        self._latest: dict[str, FactorSnapshot] = {}
        self._series: dict[str, deque[FactorSnapshot]] = defaultdict(lambda: deque(maxlen=1000))

    def update(self, tick: Tick, *, sector: str = "Other") -> FactorSnapshot:
        symbol = tick.symbol.upper().strip()
        ts = tick.timestamp
        price = float(tick.price)
        volume = max(0.0, float(tick.size))
        if not math.isfinite(price) or price <= 0:
            raise ValueError("tick price must be finite and positive")

        if self._session_date.get(symbol) != ts.date():
            previous = self._latest.get(symbol)
            self._previous_close[symbol] = previous.price if previous else price
            self._session_date[symbol] = ts.date()
            self._session_start[symbol] = ts
            self._open[symbol] = price
            self._pv[symbol] = 0.0
            self._volume_sum[symbol] = 0.0
            self._or_high[symbol] = price
            self._or_low[symbol] = price
            self._volumes[symbol].clear()

        history = self._prices[symbol]
        history.append((ts, price))
        cutoff = ts - self._roc_window
        while len(history) > 2 and history[1][0] <= cutoff:
            history.popleft()
        reference = next((p for event_ts, p in reversed(history) if event_ts <= cutoff), None)
        roc = None if reference is None else price / reference - 1.0

        historical_volumes = self._volumes[symbol]
        baseline = median(historical_volumes) if len(historical_volumes) >= 5 else None
        rvol = None if not baseline or volume <= 0 else volume / baseline
        if volume > 0:
            historical_volumes.append(volume)
            self._pv[symbol] += price * volume
            self._volume_sum[symbol] += volume
        else:
            self._pv[symbol] += price
            self._volume_sum[symbol] += 1.0
        vwap = self._pv[symbol] / self._volume_sum[symbol]
        vwap_distance = price / vwap - 1.0 if vwap else None

        opening_elapsed = ts - self._session_start[symbol]
        if opening_elapsed <= self._opening_range:
            self._or_high[symbol] = max(self._or_high[symbol], price)
            self._or_low[symbol] = min(self._or_low[symbol], price)
        state = "Inside"
        if opening_elapsed > self._opening_range and price > self._or_high[symbol]:
            state = "Bull Breakout"
        elif opening_elapsed > self._opening_range and price < self._or_low[symbol]:
            state = "Bear Breakdown"

        previous_close = self._previous_close[symbol]
        gap = self._open[symbol] / previous_close - 1.0 if previous_close else None
        snapshot = FactorSnapshot(
            symbol=symbol,
            timestamp=ts,
            price=price,
            volume=volume,
            sector=sector or "Other",
            roc=roc,
            rvol=rvol,
            vwap=vwap,
            vwap_distance=vwap_distance,
            gap=gap,
            opening_range_high=self._or_high[symbol],
            opening_range_low=self._or_low[symbol],
            opening_range_state=state,
        )
        self._latest[symbol] = snapshot
        self._series[symbol].append(snapshot)
        return snapshot

    def ranked(self) -> list[FactorSnapshot]:
        ordered = sorted(
            self._latest.values(),
            key=lambda record: record.roc if record.roc is not None else float("-inf"),
            reverse=True,
        )
        return [replace(record, rank=index) for index, record in enumerate(ordered, start=1)]

    def history(self, symbol: str) -> tuple[FactorSnapshot, ...]:
        return tuple(self._series[symbol.upper()])

    def reset(self) -> None:
        self.__init__(int(self._roc_window.total_seconds()), int(self._opening_range.total_seconds() / 60))
