"""Rolling train/test walk-forward validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any, cast

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.research.application.optimizer import GridSearchOptimizer
from rdqp.research.domain.models import (
    OptimizationObjective,
    ParameterRange,
    WalkForwardFold,
    WalkForwardResult,
)
from rdqp.strategies.application.backtester import BacktestEngine
from rdqp.strategies.domain.models import StrategyDefinition


class WalkForwardEngine:
    """Run expanding-window walk-forward optimization and validation."""

    def __init__(self) -> None:
        self._optimizer = GridSearchOptimizer()
        self._backtester = BacktestEngine()

    def run(
        self,
        definition: StrategyDefinition,
        histories: Mapping[str, Sequence[FactorSnapshot]],
        ranges: Sequence[ParameterRange],
        train_fraction: float = 0.6,
        folds: int = 3,
        objective: OptimizationObjective = OptimizationObjective.SHARPE,
    ) -> WalkForwardResult:
        timestamps = sorted({item.timestamp for history in histories.values() for item in history})
        if len(timestamps) < 4 or folds < 1:
            return WalkForwardResult((), 0.0, 0.0)

        train_size = max(2, int(len(timestamps) * train_fraction))
        remaining = len(timestamps) - train_size
        test_size = max(1, remaining // folds)
        fold_results: list[WalkForwardFold] = []

        for fold in range(folds):
            train_end_index = min(
                train_size + fold * test_size,
                len(timestamps) - 1,
            )
            test_end_index = min(
                train_end_index + test_size,
                len(timestamps) - 1,
            )
            if train_end_index >= test_end_index:
                break

            train_start = timestamps[0]
            train_end = timestamps[train_end_index]
            test_start = timestamps[train_end_index + 1]
            test_end = timestamps[test_end_index]

            train = self._slice(histories, train_start, train_end)
            test = self._slice(histories, test_start, test_end)

            optimized = self._optimizer.run(
                definition,
                train,
                ranges,
                objective,
            )
            if optimized.best_trial is None:
                continue

            selected = optimized.best_trial.parameters
            configured = replace(
                definition,
                **cast(dict[str, Any], selected),
            )
            out_result = self._backtester.run(configured, test)

            fold_results.append(
                WalkForwardFold(
                    fold + 1,
                    train_start,
                    train_end,
                    test_start,
                    test_end,
                    selected,
                    optimized.best_trial.score,
                    out_result,
                )
            )

        returns = [item.out_of_sample_result.metrics.total_return for item in fold_results]

        combined = 1.0
        for value in returns:
            combined *= 1.0 + value

        average = sum(returns) / len(returns) if returns else 0.0
        return WalkForwardResult(
            tuple(fold_results),
            combined - 1.0 if returns else 0.0,
            average,
        )

    @staticmethod
    def _slice(
        histories: Mapping[str, Sequence[FactorSnapshot]],
        start: datetime,
        end: datetime,
    ) -> dict[str, tuple[FactorSnapshot, ...]]:
        return {
            symbol: tuple(item for item in history if start <= item.timestamp <= end)
            for symbol, history in histories.items()
        }
