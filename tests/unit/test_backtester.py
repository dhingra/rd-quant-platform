from datetime import datetime, timedelta, timezone

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.strategies import BacktestEngine, RuleOperator, StrategyDefinition, StrategyRule


def snapshot(t, price, roc):
    return FactorSnapshot(
        symbol="AAPL", timestamp=t, price=price, volume=1000, sector="Technology",
        roc=roc, rvol=2.0, vwap=price - 1, vwap_distance=0.01, gap=0.0,
        opening_range_high=None, opening_range_low=None, opening_range_state="inside", rank=1,
    )


def test_backtest_generates_trade_and_metrics():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    history = [
        snapshot(start, 100, 0.02),
        snapshot(start + timedelta(minutes=1), 105, 0.03),
        snapshot(start + timedelta(minutes=2), 104, -0.01),
    ]
    strategy = StrategyDefinition(
        name="test",
        entry_rules=(StrategyRule("roc_pct", RuleOperator.GT, 1.0),),
        exit_rules=(StrategyRule("roc_pct", RuleOperator.LT, 0.0),),
        initial_capital=10_000,
        allocation_pct=0.5,
    )
    result = BacktestEngine().run(strategy, {"AAPL": history})
    assert result.metrics.trade_count == 1
    assert result.trades[0].pnl > 0
    assert result.metrics.final_equity > 10_000
