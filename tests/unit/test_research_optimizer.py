from datetime import UTC, datetime, timedelta

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.research.application.optimizer import GridSearchOptimizer
from rdqp.research.domain.models import OptimizationObjective, ParameterRange
from rdqp.strategies.domain.models import RuleOperator, StrategyDefinition, StrategyRule


def snapshot(seconds: int, price: float, roc: float) -> FactorSnapshot:
    return FactorSnapshot(
        "AAPL", datetime(2026, 1, 2, tzinfo=UTC) + timedelta(seconds=seconds),
        price, 100.0, "Technology", roc, 2.0, price - 1, 0.01, 0.0,
        price + 1, price - 1, "Inside", 1,
    )


def test_grid_search_returns_ranked_trials() -> None:
    strategy = StrategyDefinition(
        "test", (StrategyRule("roc_pct", RuleOperator.GT, 0.0),),
        stop_loss_pct=0.02, take_profit_pct=0.05,
    )
    histories = {"AAPL": (snapshot(0, 100, 0.01), snapshot(60, 106, 0.02))}
    result = GridSearchOptimizer().run(
        strategy,
        histories,
        (ParameterRange("take_profit_pct", (0.03, 0.05)),),
        OptimizationObjective.TOTAL_RETURN,
    )
    assert len(result.trials) == 2
    assert result.best_trial is not None
    assert result.trials[0].score >= result.trials[1].score
