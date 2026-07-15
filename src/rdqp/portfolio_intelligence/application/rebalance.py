"""Target-weight rebalance planning."""

from __future__ import annotations

from rdqp.portfolio_intelligence.domain import RebalancePlan, RebalanceTrade


def build_rebalance_plan(
    current_weights: dict[str, float],
    target_weights: dict[str, float],
    portfolio_value: float,
    cost_bps: float = 0.0,
    minimum_notional: float = 0.0,
) -> RebalancePlan:
    if portfolio_value < 0 or cost_bps < 0 or minimum_notional < 0:
        raise ValueError("portfolio value, costs, and minimum notional cannot be negative")
    symbols = sorted(set(current_weights) | set(target_weights))
    trades = []
    for symbol in symbols:
        current = current_weights.get(symbol, 0.0)
        target = target_weights.get(symbol, 0.0)
        change = target - current
        notional = change * portfolio_value
        if abs(notional) < minimum_notional:
            continue
        cost = abs(notional) * cost_bps / 10_000
        trades.append(RebalanceTrade(symbol, current, target, change, notional, cost))
    turnover = sum(abs(trade.weight_change) for trade in trades) / 2
    return RebalancePlan(
        portfolio_value, turnover, sum(trade.estimated_cost for trade in trades), tuple(trades)
    )
