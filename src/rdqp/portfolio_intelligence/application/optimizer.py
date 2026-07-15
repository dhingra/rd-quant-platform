"""Constrained long-only portfolio optimization."""

from __future__ import annotations

from math import sqrt

from rdqp.portfolio_intelligence.application.math import (
    covariance_matrix,
    dot,
    matvec,
    portfolio_variance,
    project_weights,
)
from rdqp.portfolio_intelligence.domain import (
    OptimizationObjective,
    PortfolioConstraints,
    PortfolioSolution,
    PortfolioWeight,
)


class PortfolioOptimizer:
    def optimize(
        self,
        returns: dict[str, list[float]],
        objective: OptimizationObjective,
        constraints: PortfolioConstraints = PortfolioConstraints(),
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> PortfolioSolution:
        symbols = sorted(returns)
        if len(symbols) < 2:
            raise ValueError("at least two symbols are required")
        lengths = {len(returns[symbol]) for symbol in symbols}
        if len(lengths) != 1 or next(iter(lengths)) < 2:
            raise ValueError("return series must have equal length and at least two observations")

        rows = [
            [returns[symbol][index] for symbol in symbols] for index in range(next(iter(lengths)))
        ]
        means = [
            sum(returns[symbol]) / len(returns[symbol]) * periods_per_year for symbol in symbols
        ]
        covariance = covariance_matrix(rows)
        covariance = [[value * periods_per_year for value in row] for row in covariance]
        weights = [1.0 / len(symbols)] * len(symbols)

        for _ in range(constraints.iterations):
            sigma_w = matvec(covariance, weights)
            variance = max(dot(weights, sigma_w), 1e-16)
            volatility = sqrt(variance)
            expected = dot(weights, means)

            if objective is OptimizationObjective.MINIMUM_VOLATILITY:
                gradient = [2.0 * value for value in sigma_w]
            elif objective is OptimizationObjective.MAXIMUM_SHARPE:
                excess = expected - risk_free_rate
                gradient = [
                    -(means[i] * volatility - excess * sigma_w[i] / volatility) / variance
                    for i in range(len(weights))
                ]
            else:
                target = constraints.target_return
                if target is None:
                    raise ValueError("target_return is required for TARGET_RETURN")
                penalty = 50.0 * (expected - target)
                gradient = [
                    2.0 * sigma_w[i] + 2.0 * penalty * means[i] for i in range(len(weights))
                ]

            weights = project_weights(
                [weights[i] - constraints.learning_rate * gradient[i] for i in range(len(weights))],
                constraints.min_weight,
                constraints.max_weight,
            )

        expected = dot(weights, means)
        volatility = sqrt(max(portfolio_variance(weights, covariance), 0.0))
        sharpe = (expected - risk_free_rate) / volatility if volatility else 0.0
        return PortfolioSolution(
            objective,
            tuple(
                PortfolioWeight(symbol, weight)
                for symbol, weight in zip(symbols, weights, strict=True)
            ),
            expected,
            volatility,
            sharpe,
        )
