"""Strategy deployment scorecards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from rdqp.research.application.metrics import extended_metrics
from rdqp.strategies.domain.models import BacktestResult


class ReadinessStatus(StrEnum):
    NOT_READY = "NOT_READY"
    REVIEW = "REVIEW"
    PAPER_READY = "PAPER_READY"


@dataclass(frozen=True, slots=True)
class StrategyScorecard:
    strategy_name: str
    score: int
    status: ReadinessStatus
    checks: dict[str, bool]
    total_return: float
    max_drawdown: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    profit_factor: float | None
    win_rate: float
    trade_count: int
    reasons: tuple[str, ...]


class ScorecardEngine:
    """Evaluate a backtest against explicit paper-deployment gates."""

    def evaluate(
        self,
        result: BacktestResult,
        *,
        minimum_trades: int = 10,
        maximum_drawdown: float = 0.20,
        minimum_sharpe: float = 0.75,
        minimum_profit_factor: float = 1.10,
    ) -> StrategyScorecard:
        metrics = result.metrics
        extended = extended_metrics(result)
        checks = {
            "positive_return": metrics.total_return > 0,
            "enough_trades": metrics.trade_count >= minimum_trades,
            "drawdown_controlled": abs(metrics.max_drawdown) <= maximum_drawdown,
            "sharpe_acceptable": (
                metrics.sharpe_ratio is not None and metrics.sharpe_ratio >= minimum_sharpe
            ),
            "profit_factor_acceptable": (
                metrics.profit_factor is not None and metrics.profit_factor >= minimum_profit_factor
            ),
        }
        score = round(sum(checks.values()) / len(checks) * 100)
        if score >= 80:
            status = ReadinessStatus.PAPER_READY
        elif score >= 60:
            status = ReadinessStatus.REVIEW
        else:
            status = ReadinessStatus.NOT_READY
        reasons = tuple(name.replace("_", " ") for name, passed in checks.items() if not passed)
        return StrategyScorecard(
            strategy_name=result.strategy_name,
            score=score,
            status=status,
            checks=checks,
            total_return=metrics.total_return,
            max_drawdown=metrics.max_drawdown,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=extended.sortino_ratio,
            profit_factor=metrics.profit_factor,
            win_rate=metrics.win_rate,
            trade_count=metrics.trade_count,
            reasons=reasons,
        )
