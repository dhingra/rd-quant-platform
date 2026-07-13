from datetime import UTC, datetime

import pytest

from rdqp.market.domain.models import Tick
from rdqp.platform.eventbus.bus import EventBus
from rdqp.platform.eventbus.events import TickReceived


@pytest.mark.asyncio
async def test_event_bus_dispatches_sync_and_async_handlers() -> None:
    bus = EventBus()
    observed: list[str] = []

    def sync_handler(event: TickReceived) -> None:
        observed.append(f"sync:{event.tick.symbol}")

    async def async_handler(event: TickReceived) -> None:
        observed.append(f"async:{event.tick.symbol}")

    bus.subscribe(TickReceived, sync_handler)
    bus.subscribe(TickReceived, async_handler)
    event = TickReceived(tick=Tick("NVDA", datetime.now(UTC), 100))

    failures = await bus.publish(event)

    assert failures == []
    assert observed == ["sync:NVDA", "async:NVDA"]


@pytest.mark.asyncio
async def test_event_bus_isolates_handler_failure() -> None:
    bus = EventBus()
    observed: list[str] = []

    def broken(_: TickReceived) -> None:
        raise RuntimeError("boom")

    def healthy(_: TickReceived) -> None:
        observed.append("healthy")

    bus.subscribe(TickReceived, broken)
    bus.subscribe(TickReceived, healthy)
    event = TickReceived(tick=Tick("AMD", datetime.now(UTC), 100))

    failures = await bus.publish(event)

    assert len(failures) == 1
    assert observed == ["healthy"]
