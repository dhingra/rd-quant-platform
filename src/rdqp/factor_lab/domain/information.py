"""Immutable models for factor predictive-power research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ForwardReturnObservation:
    """Realized forward return aligned to a factor formation timestamp."""

    symbol: str
    timestamp: datetime
    horizon: int
    return_value: float

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        if self.horizon <= 0:
            raise ValueError("horizon must be positive")
        object.__setattr__(self, "symbol", self.symbol.upper())


@dataclass(frozen=True, slots=True)
class InformationCoefficientPoint:
    """Pearson and rank IC for one factor cross-section."""

    factor: str
    timestamp: datetime
    horizon: int
    ic: float | None
    rank_ic: float | None
    observations: int


@dataclass(frozen=True, slots=True)
class InformationCoefficientSeries:
    """Time series and aggregate statistics for factor IC observations."""

    factor: str
    horizon: int
    points: tuple[InformationCoefficientPoint, ...]
    mean_ic: float | None
    mean_rank_ic: float | None
    ic_information_ratio: float | None
    rank_ic_information_ratio: float | None
    ic_hit_rate: float | None
    rank_ic_hit_rate: float | None


@dataclass(frozen=True, slots=True)
class QuantileBucket:
    """Forward-return summary for one ordered factor bucket."""

    bucket: int
    label: str
    observations: int
    mean_return: float | None
    median_return: float | None


@dataclass(frozen=True, slots=True)
class QuantileAnalysis:
    """Quintile or decile return analysis for one cross-section."""

    factor: str
    timestamp: datetime
    horizon: int
    bucket_count: int
    buckets: tuple[QuantileBucket, ...]
    long_short_spread: float | None
    monotonicity: float | None


@dataclass(frozen=True, slots=True)
class FactorDecayPoint:
    """Average predictive strength at one forward-return horizon."""

    horizon: int
    mean_ic: float | None
    mean_rank_ic: float | None
    cross_sections: int
    observations: int


@dataclass(frozen=True, slots=True)
class FactorDecayProfile:
    """Predictive-strength decay across multiple horizons."""

    factor: str
    points: tuple[FactorDecayPoint, ...]


@dataclass(frozen=True, slots=True)
class FactorResearchReport:
    """Combined IC, quantile, and decay output for downstream reporting."""

    factor: str
    ic_series: tuple[InformationCoefficientSeries, ...]
    quantile_analyses: tuple[QuantileAnalysis, ...]
    decay: FactorDecayProfile
