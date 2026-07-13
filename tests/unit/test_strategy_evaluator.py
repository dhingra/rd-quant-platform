from datetime import UTC, datetime

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.strategies import RuleOperator, StrategyRule, evaluate_rule


def snap(**overrides):
    values = dict(
        symbol="AAPL",
        timestamp=datetime.now(UTC),
        price=101.0,
        volume=1000,
        sector="Technology",
        roc=0.012,
        rvol=2.0,
        vwap=100.0,
        vwap_distance=0.01,
        gap=0.02,
        opening_range_high=100.5,
        opening_range_low=99.0,
        opening_range_state="breakout",
        rank=1,
    )
    values.update(overrides)
    return FactorSnapshot(**values)


def test_numeric_and_boolean_rules():
    item = snap()
    assert evaluate_rule(item, StrategyRule("roc_pct", RuleOperator.GT, 1.0))
    assert evaluate_rule(item, StrategyRule("above_vwap", RuleOperator.IS_TRUE, True))
    assert evaluate_rule(item, StrategyRule("orb_breakout", RuleOperator.IS_TRUE, True))
    assert not evaluate_rule(item, StrategyRule("rank", RuleOperator.GT, 5))
