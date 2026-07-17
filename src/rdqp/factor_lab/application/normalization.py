"""Cross-sectional winsorization and normalization services."""

from __future__ import annotations

from collections.abc import Iterable
from math import sqrt
from statistics import fmean

from rdqp.factor_lab.domain.models import (
    FactorCrossSection,
    FactorDefinition,
    FactorObservation,
    FactorScore,
    NormalizationMethod,
)


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("cannot calculate quantile of an empty sequence")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def winsorize(
    values: Iterable[float],
    lower: float = 0.01,
    upper: float = 0.99,
) -> tuple[float, ...]:
    """Clip values at interpolated cross-sectional quantile bounds."""

    data = list(values)
    if not data:
        return ()
    if not 0.0 <= lower < upper <= 1.0:
        raise ValueError("winsor bounds must satisfy 0 <= lower < upper <= 1")
    floor = _quantile(data, lower)
    ceiling = _quantile(data, upper)
    return tuple(min(max(value, floor), ceiling) for value in data)


def zscores(values: Iterable[float]) -> tuple[float, ...]:
    """Return population z-scores; constant inputs map to zero."""

    data = list(values)
    if not data:
        return ()
    mean = fmean(data)
    variance = fmean((value - mean) ** 2 for value in data)
    if variance == 0.0:
        return tuple(0.0 for _ in data)
    deviation = sqrt(variance)
    return tuple((value - mean) / deviation for value in data)


def percentile_ranks(values: Iterable[float]) -> tuple[float, ...]:
    """Return tie-aware percentile ranks in the inclusive range [0, 1]."""

    data = list(values)
    if not data:
        return ()
    if len(data) == 1:
        return (0.5,)

    ordered = sorted((value, index) for index, value in enumerate(data))
    ranks = [0.0] * len(data)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        average_rank = (cursor + end - 1) / 2
        percentile = average_rank / (len(data) - 1)
        for _, original_index in ordered[cursor:end]:
            ranks[original_index] = percentile
        cursor = end
    return tuple(ranks)


class FactorNormalizer:
    """Build normalized cross-sections from symbol observations."""

    def normalize(
        self,
        definition: FactorDefinition,
        observations: Iterable[FactorObservation],
        method: NormalizationMethod = NormalizationMethod.ZSCORE,
    ) -> FactorCrossSection:
        rows = list(observations)
        if not rows:
            raise ValueError("at least one observation is required")
        timestamps = {row.timestamp for row in rows}
        if len(timestamps) != 1:
            raise ValueError("all observations must share one timestamp")

        available = [
            (row.symbol, value)
            for row in rows
            if (value := row.values.get(definition.name)) is not None
        ]
        raw_values = [value for _, value in available]
        clipped = winsorize(
            raw_values,
            definition.winsor_lower,
            definition.winsor_upper,
        )
        percentiles = percentile_ranks(clipped)

        if method is NormalizationMethod.ZSCORE:
            normalized = zscores(clipped)
        elif method is NormalizationMethod.PERCENTILE:
            normalized = percentiles
        else:
            normalized = clipped

        direction = 1.0 if definition.higher_is_better else -1.0
        scores = tuple(
            FactorScore(
                symbol=symbol,
                factor=definition.name,
                raw_value=raw,
                winsorized_value=bounded,
                score=score * direction,
                percentile=(percentile if direction > 0 else 1.0 - percentile),
            )
            for (symbol, raw), bounded, score, percentile in zip(
                available,
                clipped,
                normalized,
                percentiles,
                strict=True,
            )
        )
        return FactorCrossSection(
            factor=definition,
            timestamp=rows[0].timestamp,
            method=method,
            scores=scores,
        )
