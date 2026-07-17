"""Pairwise factor correlation analysis."""

from __future__ import annotations

from collections.abc import Iterable
from math import sqrt
from statistics import fmean

from rdqp.factor_lab.domain.models import (
    CorrelationCell,
    FactorCorrelationMatrix,
    FactorObservation,
)


def pearson_correlation(left: Iterable[float], right: Iterable[float]) -> float | None:
    """Calculate Pearson correlation, returning None for invalid/constant samples."""

    x = list(left)
    y = list(right)
    if len(x) != len(y):
        raise ValueError("correlation inputs must have equal length")
    if len(x) < 2:
        return None
    x_mean = fmean(x)
    y_mean = fmean(y)
    covariance = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y, strict=True))
    x_variance = sum((a - x_mean) ** 2 for a in x)
    y_variance = sum((b - y_mean) ** 2 for b in y)
    denominator = sqrt(x_variance * y_variance)
    if denominator == 0.0:
        return None
    return covariance / denominator


class FactorCorrelationAnalyzer:
    """Build pairwise correlations using symbols with values for both factors."""

    def analyze(
        self,
        observations: Iterable[FactorObservation],
        factors: Iterable[str] | None = None,
    ) -> FactorCorrelationMatrix:
        rows = list(observations)
        names = tuple(
            dict.fromkeys(
                factors
                if factors is not None
                else sorted({name for row in rows for name in row.values})
            )
        )
        cells: list[CorrelationCell] = []

        for left in names:
            for right in names:
                pairs = [
                    (left_value, right_value)
                    for row in rows
                    if (left_value := row.values.get(left)) is not None
                    and (right_value := row.values.get(right)) is not None
                ]
                correlation = pearson_correlation(
                    (pair[0] for pair in pairs),
                    (pair[1] for pair in pairs),
                )
                cells.append(
                    CorrelationCell(
                        left=left,
                        right=right,
                        correlation=correlation,
                        observations=len(pairs),
                    )
                )
        return FactorCorrelationMatrix(names, tuple(cells))
