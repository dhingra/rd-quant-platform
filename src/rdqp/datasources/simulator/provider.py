"""Deterministic-capable simulated market-data provider."""

from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timezone

from rdqp.market.domain.models import Tick
from rdqp.market.ports.market_data import MarketDataProvider
from rdqp.platform.config.settings import SimulatorSettings
from rdqp.platform.plugins.registry import plugin


@plugin("market_data", "simulator")
class SimulatorProvider(MarketDataProvider):
    def __init__(self, settings: SimulatorSettings, *, seed: int | None = None) -> None:
        self._settings = settings
        self._symbols: tuple[str, ...] = ()
        self._prices: dict[str, float] = {}
        self._running = False
        self._random = random.Random(seed)

    @property
    def name(self) -> str:
        return "simulator"

    async def connect(self) -> None:
        self._running = True

    async def disconnect(self) -> None:
        self._running = False

    async def subscribe(self, symbols: Sequence[str]) -> None:
        self._symbols = tuple(dict.fromkeys(symbol.upper() for symbol in symbols if symbol.strip()))
        self._prices = {
            symbol: self._settings.initial_price * self._random.uniform(0.5, 3.0)
            for symbol in self._symbols
        }

    async def _stream(self) -> AsyncIterator[Tick]:
        if not self._running:
            raise RuntimeError("provider is not connected")
        while self._running:
            for symbol in self._symbols:
                shock = self._random.gauss(0.0, self._settings.volatility)
                price = max(0.01, self._prices[symbol] * (1.0 + shock))
                self._prices[symbol] = price
                yield Tick(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc),
                    price=price,
                    size=float(self._random.randint(1, 1000)),
                    source=self.name,
                )
            await asyncio.sleep(self._settings.interval_seconds)

    def stream(self) -> AsyncIterator[Tick]:
        return self._stream()
