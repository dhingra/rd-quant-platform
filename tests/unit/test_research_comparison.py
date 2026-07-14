from datetime import UTC, datetime

from rdqp.research.application.comparison import compare_strategies
from rdqp.strategies.domain.models import BacktestResult, EquityPoint, PerformanceMetrics


def make(name: str, total_return: float) -> BacktestResult:
    now = datetime.now(UTC)
    metrics = PerformanceMetrics(
        100_000, 100_000 * (1 + total_return), total_return, 10, 0.5, 1.2, -0.1, 10, 1.0
    )
    return BacktestResult(name, (), (EquityPoint(now, 100_000),), metrics)


def test_comparison_sorts_by_return() -> None:
    rows = compare_strategies([make("B", 0.1), make("A", 0.2)])
    assert [row.strategy_name for row in rows] == ["A", "B"]
