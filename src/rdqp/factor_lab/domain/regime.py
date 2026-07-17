"""Immutable domain models for market-regime classification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TrendRegime(StrEnum):
    BULL = "bull"
    NEUTRAL = "neutral"
    BEAR = "bear"


class VolatilityRegime(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class BreadthRegime(StrEnum):
    STRONG = "strong"
    MIXED = "mixed"
    WEAK = "weak"


class RiskRegime(StrEnum):
    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    RISK_OFF = "risk_off"


@dataclass(frozen=True, slots=True)
class RegimeThresholds:
    """Configurable thresholds used by the deterministic regime engine."""

    bull_trend: float = 0.01
    bear_trend: float = -0.01
    low_volatility: float = 0.12
    high_volatility: float = 0.28
    strong_breadth: float = 0.65
    weak_breadth: float = 0.35

    def __post_init__(self) -> None:
        if self.bear_trend >= self.bull_trend:
            raise ValueError("bear_trend must be below bull_trend")
        if not 0 <= self.low_volatility < self.high_volatility:
            raise ValueError("volatility thresholds must be ordered and non-negative")
        if not 0 <= self.weak_breadth < self.strong_breadth <= 1:
            raise ValueError("breadth thresholds must satisfy 0 <= weak < strong <= 1")


@dataclass(frozen=True, slots=True)
class RegimeObservation:
    """Market inputs used to classify one timestamp."""

    timestamp: datetime
    trend_return: float
    annualized_volatility: float
    positive_breadth: float

    def __post_init__(self) -> None:
        if self.annualized_volatility < 0:
            raise ValueError("annualized_volatility cannot be negative")
        if not 0 <= self.positive_breadth <= 1:
            raise ValueError("positive_breadth must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class RegimePoint:
    """Regime classification for one timestamp."""

    timestamp: datetime
    trend: TrendRegime
    volatility: VolatilityRegime
    breadth: BreadthRegime
    risk: RiskRegime
    confidence: float


@dataclass(frozen=True, slots=True)
class RegimeTransition:
    """A change in the composite risk regime."""

    timestamp: datetime
    previous: RiskRegime
    current: RiskRegime


@dataclass(frozen=True, slots=True)
class RegimeHistory:
    """Chronological regime classifications and detected transitions."""

    points: tuple[RegimePoint, ...]
    transitions: tuple[RegimeTransition, ...]

    @property
    def current(self) -> RegimePoint | None:
        return self.points[-1] if self.points else None
