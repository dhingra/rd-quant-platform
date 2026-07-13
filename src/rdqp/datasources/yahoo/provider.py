"""Yahoo Finance adapter.

Yahoo is a delayed/polled bar source and is intended for research and dashboard
prototyping, not execution-grade tick delivery.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from datetime import UTC

from rdqp.common.exceptions import ProviderUnavailableError
from rdqp.market.domain.models import Tick
from rdqp.market.ports.market_data import MarketDataProvider
from rdqp.platform.config.settings import YahooSettings
from rdqp.platform.plugins.registry import plugin


@plugin("market_data", "yahoo")
class YahooProvider(MarketDataProvider):
    def __init__(self, settings: YahooSettings) -> None:
        self._settings = settings
        self._symbols: tuple[str, ...] = ()
        self._running = False
        self._last_seen: dict[str, object] = {}

    @property
    def name(self) -> str:
        return "yahoo"

    async def connect(self) -> None:
        try:
            import yfinance  # noqa: F401
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Install the 'yahoo' extra to use YahooProvider"
            ) from exc
        self._running = True

    async def disconnect(self) -> None:
        self._running = False

    async def subscribe(self, symbols: Sequence[str]) -> None:
        self._symbols = tuple(dict.fromkeys(symbol.upper() for symbol in symbols if symbol.strip()))

    async def _stream(self) -> AsyncIterator[Tick]:
        import yfinance as yf

        if not self._running:
            raise RuntimeError("provider is not connected")
        while self._running:
            frame = await asyncio.to_thread(
                yf.download,
                list(self._symbols),
                period=self._settings.period,
                interval=self._settings.interval,
                group_by="ticker",
                progress=False,
                threads=True,
                auto_adjust=False,
            )
            for symbol in self._symbols:
                try:
                    symbol_frame = frame[symbol] if len(self._symbols) > 1 else frame
                    row = symbol_frame.dropna(subset=["Close"]).iloc[-1]
                    timestamp = symbol_frame.dropna(subset=["Close"]).index[-1]
                    if timestamp == self._last_seen.get(symbol):
                        continue
                    self._last_seen[symbol] = timestamp
                    dt = timestamp.to_pydatetime()
                    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
                    yield Tick(
                        symbol=symbol,
                        timestamp=dt,
                        price=float(row["Close"]),
                        size=float(row.get("Volume", 0.0)),
                        source=self.name,
                    )
                except (KeyError, IndexError, TypeError, ValueError):
                    continue
            await asyncio.sleep(self._settings.poll_seconds)

    def stream(self) -> AsyncIterator[Tick]:
        return self._stream()
