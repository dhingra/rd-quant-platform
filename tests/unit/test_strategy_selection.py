from datetime import UTC, datetime

from rdqp.factor_lab import (
    BreadthRegime,
    RegimePoint,
    RiskRegime,
    StrategyRegimePerformance,
    StrategySelectionConfig,
    StrategySelectionEngine,
    TrendRegime,
    VolatilityRegime,
)


def point(regime: RiskRegime = RiskRegime.RISK_ON) -> RegimePoint:
    return RegimePoint(
        datetime(2026, 7, 17, tzinfo=UTC),
        TrendRegime.BULL,
        VolatilityRegime.LOW,
        BreadthRegime.STRONG,
        regime,
        1.0,
    )


def perf(name: str, return_: float, sharpe: float, trades: int = 20):
    return StrategyRegimePerformance(
        name,
        RiskRegime.RISK_ON,
        return_,
        sharpe,
        -0.10,
        1.8,
        trades,
    )


def test_strategy_selection_ranks_and_allocates() -> None:
    result = StrategySelectionEngine().select(
        point(),
        [perf("Momentum", 0.20, 1.8), perf("Breakout", 0.10, 1.1)],
    )
    assert result.leader is not None
    assert result.leader.strategy_name == "Momentum"
    assert len(result.allocations) == 2
    assert abs(sum(item.weight for item in result.allocations) - 1.0) < 1e-12


def test_strategy_selection_filters_hostile_and_irrelevant_regimes() -> None:
    engine = StrategySelectionEngine(StrategySelectionConfig(minimum_trades=10))
    hostile = perf("Fragile", -0.02, 0.4, trades=3)
    other = StrategyRegimePerformance(
        "Defensive", RiskRegime.RISK_OFF, 0.1, 1.0, -0.05, 1.5, 20
    )
    result = engine.select(point(), [hostile, other])
    assert len(result.recommendations) == 1
    assert not result.recommendations[0].eligible
    assert result.allocations == ()
