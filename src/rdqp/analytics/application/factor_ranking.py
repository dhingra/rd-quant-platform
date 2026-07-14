"""Weighted cross-sectional multi-factor ranking."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev

from rdqp.analytics.domain.models import FactorSnapshot


@dataclass(frozen=True, slots=True)
class FactorWeights:
    roc: float = 0.40
    rvol: float = 0.20
    vwap_distance: float = 0.20
    gap: float = 0.10
    sector_strength: float = 0.10

    def normalized(self) -> FactorWeights:
        values = [self.roc, self.rvol, self.vwap_distance, self.gap, self.sector_strength]
        if any(value < 0 for value in values):
            raise ValueError("Factor weights cannot be negative")
        total = sum(values)
        if total <= 0:
            raise ValueError("At least one factor weight must be positive")
        return FactorWeights(*(value / total for value in values))


@dataclass(frozen=True, slots=True)
class FactorScore:
    symbol: str
    score: float
    rank: int
    components: dict[str, float]


def _zscore(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    mean = fmean(values.values())
    std = pstdev(values.values()) if len(values) > 1 else 0.0
    if std == 0:
        return {key: 0.0 for key in values}
    return {key: (value - mean) / std for key, value in values.items()}


def rank_factors(
    records: list[FactorSnapshot], weights: FactorWeights | None = None
) -> tuple[FactorScore, ...]:
    selected = (weights or FactorWeights()).normalized()
    sector_values: dict[str, list[float]] = {}
    for record in records:
        if record.roc is not None:
            sector_values.setdefault(record.sector, []).append(record.roc)
    sector_means = {sector: fmean(values) for sector, values in sector_values.items()}

    raw = {
        "roc": {r.symbol: r.roc for r in records if r.roc is not None},
        "rvol": {r.symbol: r.rvol for r in records if r.rvol is not None},
        "vwap_distance": {
            r.symbol: r.vwap_distance for r in records if r.vwap_distance is not None
        },
        "gap": {r.symbol: r.gap for r in records if r.gap is not None},
        "sector_strength": {
            r.symbol: sector_means[r.sector] for r in records if r.sector in sector_means
        },
    }
    standardized = {name: _zscore(values) for name, values in raw.items()}
    scores = []
    for record in records:
        components = {
            "roc": standardized["roc"].get(record.symbol, 0.0),
            "rvol": standardized["rvol"].get(record.symbol, 0.0),
            "vwap_distance": standardized["vwap_distance"].get(record.symbol, 0.0),
            "gap": standardized["gap"].get(record.symbol, 0.0),
            "sector_strength": standardized["sector_strength"].get(record.symbol, 0.0),
        }
        score = (
            components["roc"] * selected.roc
            + components["rvol"] * selected.rvol
            + components["vwap_distance"] * selected.vwap_distance
            + components["gap"] * selected.gap
            + components["sector_strength"] * selected.sector_strength
        )
        scores.append((record.symbol, score, components))
    scores.sort(key=lambda item: item[1], reverse=True)
    return tuple(
        FactorScore(symbol=symbol, score=score, rank=index, components=components)
        for index, (symbol, score, components) in enumerate(scores, start=1)
    )
