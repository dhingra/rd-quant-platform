"""Immutable domain models for cross-sectional factor research."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType


class NormalizationMethod(StrEnum):
    """Supported cross-sectional normalization methods."""

    RAW = "raw"
    ZSCORE = "zscore"
    PERCENTILE = "percentile"


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    """Metadata describing a research factor."""

    name: str
    description: str = ""
    higher_is_better: bool = True
    winsor_lower: float = 0.01
    winsor_upper: float = 0.99

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("factor name cannot be empty")
        if not 0.0 <= self.winsor_lower < self.winsor_upper <= 1.0:
            raise ValueError("winsor bounds must satisfy 0 <= lower < upper <= 1")


@dataclass(frozen=True, slots=True)
class FactorObservation:
    """One symbol's raw factor values at a point in time."""

    symbol: str
    timestamp: datetime
    values: Mapping[str, float | None]

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True, slots=True)
class FactorScore:
    """Raw and normalized value for a symbol-factor pair."""

    symbol: str
    factor: str
    raw_value: float
    winsorized_value: float
    score: float
    percentile: float


@dataclass(frozen=True, slots=True)
class FactorCrossSection:
    """Normalized scores for a single factor and timestamp."""

    factor: FactorDefinition
    timestamp: datetime
    method: NormalizationMethod
    scores: tuple[FactorScore, ...]


@dataclass(frozen=True, slots=True)
class CorrelationCell:
    """Pairwise factor correlation."""

    left: str
    right: str
    correlation: float | None
    observations: int


@dataclass(frozen=True, slots=True)
class FactorCorrelationMatrix:
    """Long-form correlation matrix for UI and export consumers."""

    factors: tuple[str, ...]
    cells: tuple[CorrelationCell, ...]
