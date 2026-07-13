from datetime import UTC, datetime, timedelta

from rdqp.research.application.monte_carlo import MonteCarloEngine
from rdqp.strategies.domain.models import BacktestResult, EquityPoint, PerformanceMetrics, TradeRecord


def test_bootstrap_produces_non_degenerate_distribution() -> None:
    start = datetime.now(UTC)
    trades = tuple(
        TradeRecord("A", start, start + timedelta(hours=1), 100, 101, 1, value * 100, value, "x")
        for value in (0.10, -0.05, 0.02, -0.01)
    )
    metrics = PerformanceMetrics(100_000, 105_000, 0.05, 4, 0.5, 1.2, -0.1, 10, 1.0)
    result = BacktestResult("x", trades, (EquityPoint(start, 100_000),), metrics)
    summary = MonteCarloEngine().run(result, simulations=100, seed=1)
    assert len(set(summary.final_equities)) > 1
