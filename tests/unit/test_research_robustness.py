from datetime import UTC, datetime

from rdqp.research.application.robustness import analyze_robustness
from rdqp.research.domain.models import OptimizationObjective, OptimizationResult, OptimizationTrial
from rdqp.strategies.domain.models import BacktestResult, EquityPoint, PerformanceMetrics


def result(score: float) -> OptimizationTrial:
    now = datetime.now(UTC)
    metrics = PerformanceMetrics(100_000, 101_000, 0.01, 10, 0.5, 1.2, -0.05, 10, score)
    backtest = BacktestResult("x", (), (EquityPoint(now, 100_000),), metrics)
    return OptimizationTrial({}, score, backtest)


def test_robustness_summarizes_trials() -> None:
    optimization = OptimizationResult(
        OptimizationObjective.SHARPE,
        (result(1.0), result(0.8), result(-0.2)),
        result(1.0),
    )
    summary = analyze_robustness(optimization)
    assert summary.trial_count == 3
    assert summary.positive_trials == 2
    assert 0 <= summary.stability_score <= 100
