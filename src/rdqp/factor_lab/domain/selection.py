"""Immutable models for regime-aware strategy selection."""

from __future__ import annotations

from dataclasses import dataclass

from rdqp.factor_lab.domain.regime import RiskRegime


@dataclass(frozen=True, slots=True)
class StrategyRegimePerformance:
    """Observed strategy performance in one composite market regime."""

    strategy_name: str
    regime: RiskRegime
    total_return: float
    sharpe_ratio: float | None
    max_drawdown: float
    profit_factor: float | None
    trade_count: int

    def __post_init__(self) -> None:
        if not self.strategy_name.strip():
            raise ValueError("strategy_name cannot be empty")
        if self.trade_count < 0:
            raise ValueError("trade_count cannot be negative")
        if self.max_drawdown > 0:
            raise ValueError("max_drawdown must be zero or negative")


@dataclass(frozen=True, slots=True)
class StrategySelectionConfig:
    """Scoring, eligibility, and ensemble-allocation settings."""

    return_weight: float = 0.35
    sharpe_weight: float = 0.30
    drawdown_weight: float = 0.20
    profit_factor_weight: float = 0.15
    minimum_trades: int = 5
    maximum_drawdown: float = -0.30
    maximum_strategies: int = 3
    disable_negative_regime_return: bool = True

    def __post_init__(self) -> None:
        weights = (
            self.return_weight,
            self.sharpe_weight,
            self.drawdown_weight,
            self.profit_factor_weight,
        )
        if any(value < 0 for value in weights) or sum(weights) <= 0:
            raise ValueError("selection weights must be non-negative with a positive sum")
        if self.minimum_trades < 0:
            raise ValueError("minimum_trades cannot be negative")
        if not -1 <= self.maximum_drawdown <= 0:
            raise ValueError("maximum_drawdown must be in [-1, 0]")
        if self.maximum_strategies < 1:
            raise ValueError("maximum_strategies must be positive")


@dataclass(frozen=True, slots=True)
class StrategyRecommendation:
    """A scored strategy and its deployment eligibility."""

    strategy_name: str
    score: float
    eligible: bool
    reasons: tuple[str, ...]
    regime: RiskRegime
    confidence: float


@dataclass(frozen=True, slots=True)
class StrategyAllocation:
    strategy_name: str
    weight: float
    score: float


@dataclass(frozen=True, slots=True)
class StrategySelectionResult:
    """Ranked recommendations and normalized ensemble allocation."""

    regime: RiskRegime
    recommendations: tuple[StrategyRecommendation, ...]
    allocations: tuple[StrategyAllocation, ...]

    @property
    def leader(self) -> StrategyRecommendation | None:
        return self.recommendations[0] if self.recommendations else None
