"""Composition root for RD Quant Platform."""

from rdqp.datasources.ibkr.provider import IBKRProvider
from rdqp.datasources.simulator.provider import SimulatorProvider
from rdqp.datasources.yahoo.provider import YahooProvider
from rdqp.market.application.stream_service import MarketStreamService
from rdqp.market.ports.market_data import MarketDataProvider
from rdqp.platform.config.settings import Settings
from rdqp.platform.di.container import Container
from rdqp.platform.eventbus.bus import EventBus


def build_container(settings: Settings) -> Container:
    container = Container()
    container.register_instance(Settings, settings)
    container.register_instance(EventBus, EventBus())

    def provider_factory(_: Container) -> MarketDataProvider:
        provider = settings.market_data.provider.lower()
        if provider == "simulator":
            return SimulatorProvider(settings.market_data.simulator)
        if provider == "yahoo":
            return YahooProvider(settings.market_data.yahoo)
        if provider == "ibkr":
            return IBKRProvider(settings.market_data.ibkr)
        raise ValueError(f"Unknown market-data provider: {provider}")

    container.register_factory(MarketDataProvider, provider_factory)
    container.register_factory(
        MarketStreamService,
        lambda c: MarketStreamService(c.resolve(MarketDataProvider), c.resolve(EventBus)),
    )
    return container
