"""Command-line smoke test for the platform foundation."""

import argparse
import asyncio

from rdqp.app import build_container
from rdqp.market.application.stream_service import MarketStreamService
from rdqp.platform.config.settings import load_settings
from rdqp.platform.eventbus.bus import EventBus
from rdqp.platform.eventbus.events import TickReceived
from rdqp.platform.logging.setup import configure_logging


async def _run(config: str, ticks: int) -> None:
    settings = load_settings(config)
    configure_logging(level=settings.app.log_level)
    container = build_container(settings)
    bus = container.resolve(EventBus)

    def print_tick(event: TickReceived) -> None:
        tick = event.tick
        print(f"{tick.timestamp.isoformat()} {tick.symbol:<6} {tick.price:>10.4f} {tick.source}")

    bus.subscribe(TickReceived, print_tick)
    service = container.resolve(MarketStreamService)
    await service.run(settings.market_data.watchlist, max_ticks=ticks)


def main() -> None:
    parser = argparse.ArgumentParser(description="RD Quant Platform foundation smoke test")
    parser.add_argument("--config", default="config/app.yaml")
    parser.add_argument("--ticks", type=int, default=20)
    args = parser.parse_args()
    asyncio.run(_run(args.config, args.ticks))


if __name__ == "__main__":
    main()
