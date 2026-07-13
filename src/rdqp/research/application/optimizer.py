"""Deterministic grid-search optimizer for strategy risk parameters."""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any, cast

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.research.domain.models import (
    OptimizationObjective,
    OptimizationResult,
    OptimizationTrial,
    ParameterRange,
)
from rdqp.strategies.application.backtester import BacktestEngine
from rdqp.strategies.domain.models import BacktestResult, StrategyDefinition


class GridSearchOptimizer:
    """Search supported StrategyDefinition fields without mutating the source definition."""

    _SUPPORTED = {"allocation_pct", "stop_loss_pct", "take_profit_pct", "commission_per_trade"}

    def __init__(self, backtester: BacktestEngine | None = None) -> None:
        self._backtester = backtester or BacktestEngine()

    def run(
        self,
        definition: StrategyDefinition,
        histories: Mapping[str, Sequence[FactorSnapshot]],
        ranges: Sequence[ParameterRange],
        objective: OptimizationObjective = OptimizationObjective.SHARPE,
    ) -> OptimizationResult:
        for parameter in ranges:
            if parameter.name not in self._SUPPORTED:
                raise ValueError(f"Unsupported optimization parameter: {parameter.name}")
            if not parameter.values:
                raise ValueError(f"Parameter range is empty: {parameter.name}")

        names = [parameter.name for parameter in ranges]
        trials: list[OptimizationTrial] = []
        value_sets = [parameter.values for parameter in ranges]
        for values in itertools.product(*value_sets):
            parameters = dict(zip(names, values, strict=True))
            candidate = replace(
                definition,
                **cast(dict[str, Any], parameters),
            )
            result = self._backtester.run(candidate, histories)
            trials.append(OptimizationTrial(parameters, self.score(result, objective), result))

        reverse = objective is not OptimizationObjective.MAX_DRAWDOWN
        trials.sort(key=lambda trial: trial.score, reverse=reverse)
        return OptimizationResult(objective, tuple(trials), trials[0] if trials else None)

    @staticmethod
    def score(result: BacktestResult, objective: OptimizationObjective) -> float:
        metrics = result.metrics
        if objective is OptimizationObjective.TOTAL_RETURN:
            return metrics.total_return
        if objective is OptimizationObjective.SHARPE:
            return metrics.sharpe_ratio if metrics.sharpe_ratio is not None else float("-inf")
        if objective is OptimizationObjective.PROFIT_FACTOR:
            value = metrics.profit_factor
            if value is None:
                return float("-inf")
            return 1_000_000.0 if value == float("inf") else value
        return abs(metrics.max_drawdown)
