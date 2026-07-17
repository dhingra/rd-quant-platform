"""Regime-aware strategy scoring and ensemble allocation."""

from __future__ import annotations

from collections.abc import Sequence

from rdqp.factor_lab.domain.regime import RegimePoint
from rdqp.factor_lab.domain.selection import (
    StrategyAllocation,
    StrategyRecommendation,
    StrategyRegimePerformance,
    StrategySelectionConfig,
    StrategySelectionResult,
)


class StrategySelectionEngine:
    """Rank strategies using performance observed in the current risk regime."""

    def __init__(self, config: StrategySelectionConfig | None = None) -> None:
        self.config = config or StrategySelectionConfig()

    def select(
        self,
        regime: RegimePoint,
        performances: Sequence[StrategyRegimePerformance],
    ) -> StrategySelectionResult:
        matching = [item for item in performances if item.regime is regime.risk]
        recommendations = tuple(
            sorted(
                (self._recommend(regime, item) for item in matching),
                key=lambda item: (item.eligible, item.score, item.strategy_name),
                reverse=True,
            )
        )
        eligible = [item for item in recommendations if item.eligible][: self.config.maximum_strategies]
        positive_scores = [max(item.score, 0.0) for item in eligible]
        total = sum(positive_scores)
        if eligible and total <= 0:
            weights = [1.0 / len(eligible)] * len(eligible)
        elif total > 0:
            weights = [score / total for score in positive_scores]
        else:
            weights = []
        allocations = tuple(
            StrategyAllocation(item.strategy_name, weight, item.score)
            for item, weight in zip(eligible, weights, strict=True)
        )
        return StrategySelectionResult(regime.risk, recommendations, allocations)

    def _recommend(
        self,
        regime: RegimePoint,
        item: StrategyRegimePerformance,
    ) -> StrategyRecommendation:
        reasons: list[str] = []
        if item.trade_count < self.config.minimum_trades:
            reasons.append(f"Only {item.trade_count} trades; minimum is {self.config.minimum_trades}")
        if item.max_drawdown < self.config.maximum_drawdown:
            reasons.append("Drawdown exceeds configured limit")
        if self.config.disable_negative_regime_return and item.total_return <= 0:
            reasons.append("Non-positive return in the current regime")

        sharpe = item.sharpe_ratio or 0.0
        profit_factor = item.profit_factor or 0.0
        drawdown_quality = max(0.0, 1.0 + item.max_drawdown)
        weights = self.config
        weight_sum = (
            weights.return_weight
            + weights.sharpe_weight
            + weights.drawdown_weight
            + weights.profit_factor_weight
        )
        raw_score = (
            weights.return_weight * item.total_return
            + weights.sharpe_weight * (sharpe / 3.0)
            + weights.drawdown_weight * drawdown_quality
            + weights.profit_factor_weight * min(profit_factor / 3.0, 1.0)
        ) / weight_sum
        confidence_multiplier = 0.5 + 0.5 * regime.confidence
        score = raw_score * confidence_multiplier
        return StrategyRecommendation(
            item.strategy_name,
            score,
            not reasons,
            tuple(reasons),
            regime.risk,
            regime.confidence,
        )
