import pytest

from rdqp.datasources.simulator.provider import SimulatorProvider
from rdqp.market.application.stream_service import MarketStreamService
from rdqp.platform.config.settings import SimulatorSettings
from rdqp.platform.eventbus.bus import EventBus
from rdqp.platform.eventbus.events import TickReceived


@pytest.mark.asyncio
async def test_simulator_publishes_normalized_ticks() -> None:
    bus = EventBus()
    received: list[TickReceived] = []
    bus.subscribe(TickReceived, received.append)
    provider = SimulatorProvider(
        SimulatorSettings(interval_seconds=0.001, initial_price=100, volatility=0.001),
        seed=7,
    )
    service = MarketStreamService(provider, bus)

    count = await service.run(("AAPL", "NVDA"), max_ticks=4)

    assert count == 4
    assert [event.tick.symbol for event in received] == ["AAPL", "NVDA", "AAPL", "NVDA"]
    assert all(event.tick.source == "simulator" for event in received)
