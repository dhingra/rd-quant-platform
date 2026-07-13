"""Side-by-side strategy comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rdqp.research.application.metrics import extended_metrics
from rdqp.strategies.domain.models import BacktestResult


@dataclass(frozen=True, slots=True)
class StrategyComparisonRow:
    strategy_name: str
    total_return: float
    max_drawdown: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    profit_factor: float | None
    win_rate: float
    trade_count: int


def compare_strategies(results: Iterable[BacktestResult]) -> tuple[StrategyComparisonRow, ...]:
    rows = []
    for result in results:
        ext = extended_metrics(result)
        metrics = result.metrics
        rows.append(
            StrategyComparisonRow(
                strategy_name=result.strategy_name,
                total_return=metrics.total_return,
                max_drawdown=metrics.max_drawdown,
                sharpe_ratio=metrics.sharpe_ratio,
                sortino_ratio=ext.sortino_ratio,
                profit_factor=metrics.profit_factor,
                win_rate=metrics.win_rate,
                trade_count=metrics.trade_count,
            )
        )
    return tuple(sorted(rows, key=lambda row: row.total_return, reverse=True))
