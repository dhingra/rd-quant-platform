"""IBKR market-data adapter skeleton for Sprint 1.

The package boundary and lifecycle are implemented now; production subscription
mapping and reconnect supervision are scheduled for the provider migration sprint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from rdqp.common.exceptions import ProviderUnavailableError
from rdqp.market.domain.models import Tick
from rdqp.market.ports.market_data import MarketDataProvider
from rdqp.platform.config.settings import IBKRSettings
from rdqp.platform.plugins.registry import plugin


@plugin("market_data", "ibkr")
class IBKRProvider(MarketDataProvider):
    def __init__(self, settings: IBKRSettings) -> None:
        self._settings = settings
        self._symbols: tuple[str, ...] = ()
        self._ib: object | None = None

    @property
    def name(self) -> str:
        return "ibkr"

    async def connect(self) -> None:
        try:
            from ib_insync import IB
        except ImportError as exc:
            raise ProviderUnavailableError("Install the 'ibkr' extra to use IBKRProvider") from exc
        ib = IB()
        await ib.connectAsync(
            self._settings.host,
            self._settings.port,
            clientId=self._settings.client_id,
            readonly=True,
        )
        ib.reqMarketDataType(self._settings.market_data_type)
        self._ib = ib

    async def disconnect(self) -> None:
        if self._ib is not None:
            self._ib.disconnect()  # type: ignore[attr-defined]
            self._ib = None

    async def subscribe(self, symbols: Sequence[str]) -> None:
        self._symbols = tuple(dict.fromkeys(symbol.upper() for symbol in symbols if symbol.strip()))

    async def _stream(self) -> AsyncIterator[Tick]:
        raise NotImplementedError(
            "IBKR streaming subscription mapping is intentionally deferred to Sprint 2; "
            "the adapter package, configuration, and connection lifecycle are in place."
        )
        yield  # pragma: no cover

    def stream(self) -> AsyncIterator[Tick]:
        return self._stream()
