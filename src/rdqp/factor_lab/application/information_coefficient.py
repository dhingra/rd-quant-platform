"""Information-coefficient and rank-information-coefficient analysis."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from math import sqrt
from statistics import fmean

from rdqp.factor_lab.application.correlation import pearson_correlation
from rdqp.factor_lab.domain.information import (
    ForwardReturnObservation,
    InformationCoefficientPoint,
    InformationCoefficientSeries,
)
from rdqp.factor_lab.domain.models import FactorCrossSection


def average_ranks(values: Sequence[float]) -> tuple[float, ...]:
    """Return one-based average ranks with deterministic tie handling."""

    if not values:
        return ()
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        average = (cursor + 1 + end) / 2.0
        for _, original_index in ordered[cursor:end]:
            ranks[original_index] = average
        cursor = end
    return tuple(ranks)


def spearman_correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    """Calculate Spearman rank correlation with average ranks for ties."""

    if len(left) != len(right):
        raise ValueError("correlation inputs must have equal length")
    return pearson_correlation(average_ranks(left), average_ranks(right))


def _safe_mean(values: Sequence[float]) -> float | None:
    return fmean(values) if values else None


def _information_ratio(values: Sequence[float]) -> float | None:
    if not values:
        return None
    mean = fmean(values)
    variance = fmean((value - mean) ** 2 for value in values)
    if variance == 0.0:
        return None
    return mean / sqrt(variance)


def _hit_rate(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(value > 0.0 for value in values) / len(values)


class InformationCoefficientAnalyzer:
    """Measure factor scores against subsequently realized returns."""

    def analyze_point(
        self,
        cross_section: FactorCrossSection,
        forward_returns: Mapping[str, float] | Iterable[ForwardReturnObservation],
        horizon: int = 1,
    ) -> InformationCoefficientPoint:
        if horizon <= 0:
            raise ValueError("horizon must be positive")

        if isinstance(forward_returns, Mapping):
            returns = {symbol.upper(): value for symbol, value in forward_returns.items()}
        else:
            returns = {
                row.symbol: row.return_value
                for row in forward_returns
                if row.timestamp == cross_section.timestamp and row.horizon == horizon
            }

        pairs = [
            (score.score, returns[score.symbol])
            for score in cross_section.scores
            if score.symbol in returns
        ]
        factor_values = [pair[0] for pair in pairs]
        realized_returns = [pair[1] for pair in pairs]
        return InformationCoefficientPoint(
            factor=cross_section.factor.name,
            timestamp=cross_section.timestamp,
            horizon=horizon,
            ic=pearson_correlation(factor_values, realized_returns),
            rank_ic=spearman_correlation(factor_values, realized_returns),
            observations=len(pairs),
        )

    def analyze_series(
        self,
        cross_sections: Iterable[FactorCrossSection],
        forward_returns: Iterable[ForwardReturnObservation],
        horizon: int = 1,
    ) -> InformationCoefficientSeries:
        sections = tuple(cross_sections)
        if not sections:
            raise ValueError("at least one cross-section is required")
        factor_names = {section.factor.name for section in sections}
        if len(factor_names) != 1:
            raise ValueError("all cross-sections must represent one factor")

        returns_by_timestamp: dict[datetime, list[ForwardReturnObservation]] = defaultdict(list)
        for row in forward_returns:
            if row.horizon == horizon:
                returns_by_timestamp[row.timestamp].append(row)

        points = tuple(
            self.analyze_point(
                section,
                returns_by_timestamp.get(section.timestamp, ()),
                horizon,
            )
            for section in sorted(sections, key=lambda item: item.timestamp)
        )
        valid_ic = [point.ic for point in points if point.ic is not None]
        valid_rank_ic = [point.rank_ic for point in points if point.rank_ic is not None]
        return InformationCoefficientSeries(
            factor=sections[0].factor.name,
            horizon=horizon,
            points=points,
            mean_ic=_safe_mean(valid_ic),
            mean_rank_ic=_safe_mean(valid_rank_ic),
            ic_information_ratio=_information_ratio(valid_ic),
            rank_ic_information_ratio=_information_ratio(valid_rank_ic),
            ic_hit_rate=_hit_rate(valid_ic),
            rank_ic_hit_rate=_hit_rate(valid_rank_ic),
        )
