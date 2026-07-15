"""Immutable portfolio-intelligence domain records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OptimizationObjective(StrEnum):
    MINIMUM_VOLATILITY = "minimum_volatility"
    MAXIMUM_SHARPE = "maximum_sharpe"
    TARGET_RETURN = "target_return"


@dataclass(frozen=True, slots=True)
class PortfolioConstraints:
    min_weight: float = 0.0
    max_weight: float = 1.0
    target_return: float | None = None
    iterations: int = 2_000
    learning_rate: float = 0.05

    def __post_init__(self) -> None:
        if not 0 <= self.min_weight <= self.max_weight <= 1:
            raise ValueError("weights must satisfy 0 <= min_weight <= max_weight <= 1")
        if self.iterations <= 0:
            raise ValueError("iterations must be positive")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")


@dataclass(frozen=True, slots=True)
class PortfolioWeight:
    symbol: str
    weight: float


@dataclass(frozen=True, slots=True)
class PortfolioSolution:
    objective: OptimizationObjective
    weights: tuple[PortfolioWeight, ...]
    expected_return: float
    volatility: float
    sharpe_ratio: float


@dataclass(frozen=True, slots=True)
class RiskContribution:
    symbol: str
    weight: float
    marginal: float
    component: float
    percentage: float


@dataclass(frozen=True, slots=True)
class PortfolioRiskReport:
    expected_return: float
    volatility: float
    beta: float | None
    value_at_risk_95: float
    value_at_risk_99: float
    expected_shortfall_95: float
    maximum_drawdown: float
    contributions: tuple[RiskContribution, ...]
    correlation: tuple[tuple[float, ...], ...]


@dataclass(frozen=True, slots=True)
class StressScenario:
    name: str
    shocks: dict[str, float]


@dataclass(frozen=True, slots=True)
class StressResult:
    name: str
    pnl_fraction: float
    pnl_value: float
    contributions: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class RebalanceTrade:
    symbol: str
    current_weight: float
    target_weight: float
    weight_change: float
    notional: float
    estimated_cost: float


@dataclass(frozen=True, slots=True)
class RebalancePlan:
    portfolio_value: float
    turnover: float
    estimated_cost: float
    trades: tuple[RebalanceTrade, ...]
