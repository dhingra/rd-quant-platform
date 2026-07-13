"""Application service that bridges a provider into the event pipeline."""

import logging

from rdqp.market.ports.market_data import MarketDataProvider
from rdqp.platform.eventbus.bus import EventBus
from rdqp.platform.eventbus.events import TickReceived


class MarketStreamService:
    def __init__(self, provider: MarketDataProvider, event_bus: EventBus) -> None:
        self._provider = provider
        self._event_bus = event_bus
        self._logger = logging.getLogger(__name__)

    async def run(self, symbols: tuple[str, ...], *, max_ticks: int | None = None) -> int:
        await self._provider.connect()
        await self._provider.subscribe(symbols)
        count = 0
        try:
            async for tick in self._provider.stream():
                await self._event_bus.publish(TickReceived(tick=tick))
                count += 1
                if max_ticks is not None and count >= max_ticks:
                    break
        finally:
            await self._provider.disconnect()
        self._logger.info("market stream stopped provider=%s ticks=%s", self._provider.name, count)
        return count
