"""Deterministic portfolio stress testing."""

from __future__ import annotations

from rdqp.portfolio_intelligence.domain import StressResult, StressScenario


def run_stress_tests(
    weights: dict[str, float],
    portfolio_value: float,
    scenarios: list[StressScenario],
) -> tuple[StressResult, ...]:
    results = []
    for scenario in scenarios:
        contributions = tuple(
            (symbol, portfolio_value * weight * scenario.shocks.get(symbol, 0.0))
            for symbol, weight in sorted(weights.items())
        )
        pnl_value = sum(value for _, value in contributions)
        results.append(
            StressResult(
                scenario.name,
                pnl_value / portfolio_value if portfolio_value else 0.0,
                pnl_value,
                contributions,
            )
        )
    return tuple(results)


def market_shock(name: str, symbols: list[str], shock: float) -> StressScenario:
    return StressScenario(name, {symbol: shock for symbol in symbols})
