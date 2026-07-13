"""Strategy-rule evaluation independent of data source and UI."""

from __future__ import annotations

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.strategies.domain.models import RuleOperator, StrategyRule


def snapshot_value(snapshot: FactorSnapshot, field: str) -> object:
    values: dict[str, object] = {
        "price": snapshot.price,
        "roc_pct": None if snapshot.roc is None else snapshot.roc * 100,
        "rvol": snapshot.rvol,
        "vwap_distance_pct": None
        if snapshot.vwap_distance is None
        else snapshot.vwap_distance * 100,
        "gap_pct": None if snapshot.gap is None else snapshot.gap * 100,
        "volume": snapshot.volume,
        "rank": snapshot.rank,
        "sector": snapshot.sector,
        "above_vwap": snapshot.vwap is not None and snapshot.price > snapshot.vwap,
        "orb_breakout": snapshot.opening_range_state == "breakout",
        "orb_breakdown": snapshot.opening_range_state == "breakdown",
    }
    if field not in values:
        raise ValueError(f"Unsupported strategy field: {field}")
    return values[field]


def evaluate_rule(snapshot: FactorSnapshot, rule: StrategyRule) -> bool:
    actual = snapshot_value(snapshot, rule.field)
    if actual is None:
        return False
    if rule.operator is RuleOperator.IS_TRUE:
        return bool(actual)
    if rule.operator is RuleOperator.IS_FALSE:
        return not bool(actual)
    expected = rule.value
    if rule.operator is RuleOperator.EQ:
        return actual == expected
    if rule.operator is RuleOperator.NE:
        return actual != expected
    try:
        left = float(actual)
        right = float(expected)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    if rule.operator is RuleOperator.GT:
        return left > right
    if rule.operator is RuleOperator.GTE:
        return left >= right
    if rule.operator is RuleOperator.LT:
        return left < right
    if rule.operator is RuleOperator.LTE:
        return left <= right
    return False


def evaluate_all(snapshot: FactorSnapshot, rules: tuple[StrategyRule, ...]) -> bool:
    return bool(rules) and all(evaluate_rule(snapshot, rule) for rule in rules)
