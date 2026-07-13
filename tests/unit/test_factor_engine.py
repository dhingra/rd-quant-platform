from datetime import UTC, datetime, timedelta

import pytest

from rdqp.analytics.application.factor_engine import ReactiveFactorEngine
from rdqp.analytics.application.market_analytics import market_statistics, sector_strength
from rdqp.market.domain.models import Tick


def tick(symbol: str, seconds: int, price: float, size: float = 100) -> Tick:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return Tick(symbol, start + timedelta(seconds=seconds), price, size, "test")


def test_event_time_roc_and_rank() -> None:
    engine = ReactiveFactorEngine(120)
    engine.update(tick("AAPL", 0, 100), sector="Technology")
    engine.update(tick("MSFT", 0, 100), sector="Technology")
    aapl = engine.update(tick("AAPL", 120, 110), sector="Technology")
    engine.update(tick("MSFT", 120, 95), sector="Technology")

    assert aapl.roc == pytest.approx(0.10)
    ranked = engine.ranked()
    assert [record.symbol for record in ranked] == ["AAPL", "MSFT"]
    assert [record.rank for record in ranked] == [1, 2]


def test_statistics_and_sector_strength() -> None:
    engine = ReactiveFactorEngine(60)
    for symbol, sector, end in [("AAPL", "Technology", 102), ("JPM", "Financials", 99)]:
        engine.update(tick(symbol, 0, 100), sector=sector)
        engine.update(tick(symbol, 60, end), sector=sector)

    records = engine.ranked()
    stats = market_statistics(records)
    sectors = sector_strength(records)

    assert stats.count == 2
    assert stats.advancers == 1
    assert stats.decliners == 1
    assert sectors[0]["sector"] == "Technology"


def test_history_is_symbol_specific() -> None:
    engine = ReactiveFactorEngine(10)
    engine.update(tick("AAPL", 0, 100))
    engine.update(tick("MSFT", 0, 200))
    engine.update(tick("AAPL", 10, 101))
    assert len(engine.history("AAPL")) == 2
    assert len(engine.history("MSFT")) == 1
