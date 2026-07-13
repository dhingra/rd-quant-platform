from datetime import UTC, datetime, timedelta

from rdqp.research.application.monte_carlo import MonteCarloEngine
from rdqp.strategies.domain.models import (
    BacktestResult,
    EquityPoint,
    PerformanceMetrics,
    TradeRecord,
)


def test_monte_carlo_is_deterministic() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    trades = tuple(
        TradeRecord(
            "AAPL",
            start,
            start + timedelta(hours=1),
            100,
            100 * (1 + value),
            10,
            value * 1000,
            value,
            "test",
        )
        for value in (0.10, -0.05, 0.03)
    )
    metrics = PerformanceMetrics(100_000, 108_000, 0.08, 3, 2 / 3, 2.6, -0.05, 0, 1.0)
    result = BacktestResult("test", trades, (EquityPoint(start, 100_000),), metrics)
    first = MonteCarloEngine().run(result, 100, 3)
    second = MonteCarloEngine().run(result, 100, 3)
    assert first.final_equities == second.final_equities
    assert first.simulations == 100
