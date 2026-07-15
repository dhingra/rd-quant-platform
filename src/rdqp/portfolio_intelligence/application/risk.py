"""Portfolio risk, tail-risk, and contribution analytics."""

from __future__ import annotations

from math import sqrt

from rdqp.portfolio_intelligence.application.math import (
    correlation_matrix,
    covariance_matrix,
    dot,
    matvec,
)
from rdqp.portfolio_intelligence.domain import PortfolioRiskReport, RiskContribution


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(probability * (len(ordered) - 1))))
    return ordered[index]


def analyze_risk(
    returns: dict[str, list[float]],
    weights: dict[str, float],
    benchmark_returns: list[float] | None = None,
    periods_per_year: int = 252,
) -> PortfolioRiskReport:
    symbols = sorted(weights)
    rows = [[returns[symbol][i] for symbol in symbols] for i in range(len(returns[symbols[0]]))]
    vector = [weights[symbol] for symbol in symbols]
    means = [sum(returns[symbol]) / len(returns[symbol]) * periods_per_year for symbol in symbols]
    covariance_daily = covariance_matrix(rows)
    covariance = [[value * periods_per_year for value in row] for row in covariance_daily]
    sigma_w = matvec(covariance, vector)
    variance = max(dot(vector, sigma_w), 0.0)
    volatility = sqrt(variance)
    expected = dot(vector, means)

    contributions = []
    for symbol, weight, marginal in zip(symbols, vector, sigma_w, strict=True):
        marginal_vol = marginal / volatility if volatility else 0.0
        component = weight * marginal_vol
        contributions.append(
            RiskContribution(
                symbol,
                weight,
                marginal_vol,
                component,
                component / volatility if volatility else 0.0,
            )
        )

    portfolio_returns = [dot(vector, row) for row in rows]
    q95 = _quantile(portfolio_returns, 0.05)
    q99 = _quantile(portfolio_returns, 0.01)
    tail = [value for value in portfolio_returns if value <= q95]
    expected_shortfall = -sum(tail) / len(tail) if tail else -q95

    wealth = 1.0
    peak = 1.0
    maximum_drawdown = 0.0
    for value in portfolio_returns:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        maximum_drawdown = min(maximum_drawdown, wealth / peak - 1.0)

    beta = None
    if benchmark_returns is not None and len(benchmark_returns) == len(portfolio_returns):
        benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)
        portfolio_mean = sum(portfolio_returns) / len(portfolio_returns)
        covariance_to_market = sum(
            (p - portfolio_mean) * (b - benchmark_mean)
            for p, b in zip(portfolio_returns, benchmark_returns, strict=True)
        ) / (len(portfolio_returns) - 1)
        market_variance = sum((b - benchmark_mean) ** 2 for b in benchmark_returns) / (
            len(benchmark_returns) - 1
        )
        beta = covariance_to_market / market_variance if market_variance else 0.0

    return PortfolioRiskReport(
        expected,
        volatility,
        beta,
        -q95,
        -q99,
        expected_shortfall,
        maximum_drawdown,
        tuple(contributions),
        tuple(tuple(value for value in row) for row in correlation_matrix(covariance_daily)),
    )
