"""Immutable research and optimization domain records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from rdqp.strategies.domain.models import BacktestResult, StrategyDefinition


class OptimizationObjective(StrEnum):
    TOTAL_RETURN = "total_return"
    SHARPE = "sharpe_ratio"
    PROFIT_FACTOR = "profit_factor"
    MAX_DRAWDOWN = "max_drawdown"


@dataclass(frozen=True, slots=True)
class ParameterRange:
    name: str
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class OptimizationTrial:
    parameters: dict[str, float]
    score: float
    result: BacktestResult


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    objective: OptimizationObjective
    trials: tuple[OptimizationTrial, ...]
    best_trial: OptimizationTrial | None


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    fold: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    selected_parameters: dict[str, float]
    in_sample_score: float
    out_of_sample_result: BacktestResult


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    folds: tuple[WalkForwardFold, ...]
    combined_return: float
    average_out_of_sample_return: float


@dataclass(frozen=True, slots=True)
class MonteCarloSummary:
    simulations: int
    median_final_equity: float
    percentile_5_final_equity: float
    percentile_95_final_equity: float
    probability_of_loss: float
    median_max_drawdown: float
    final_equities: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ExtendedMetrics:
    annualized_return: float | None
    annualized_volatility: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    recovery_factor: float | None
    payoff_ratio: float | None
    average_holding_hours: float | None


@dataclass(frozen=True, slots=True)
class ResearchExperiment:
    id: int | None
    name: str
    created_at: datetime
    strategy: StrategyDefinition
    objective: str
    parameters: dict[str, float]
    metrics: dict[str, float | int | None]
    notes: str = ""
