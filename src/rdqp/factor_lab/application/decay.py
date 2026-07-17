"""Factor information-coefficient decay analysis."""

from __future__ import annotations

from collections.abc import Iterable

from rdqp.factor_lab.application.information_coefficient import InformationCoefficientAnalyzer
from rdqp.factor_lab.domain.information import (
    FactorDecayPoint,
    FactorDecayProfile,
    ForwardReturnObservation,
)
from rdqp.factor_lab.domain.models import FactorCrossSection


class FactorDecayAnalyzer:
    """Aggregate IC statistics over multiple forward-return horizons."""

    def __init__(self) -> None:
        self._ic = InformationCoefficientAnalyzer()

    def analyze(
        self,
        cross_sections: Iterable[FactorCrossSection],
        forward_returns: Iterable[ForwardReturnObservation],
        horizons: Iterable[int] | None = None,
    ) -> FactorDecayProfile:
        sections = tuple(cross_sections)
        returns = tuple(forward_returns)
        if not sections:
            raise ValueError("at least one cross-section is required")
        selected_horizons = tuple(
            sorted(set(horizons if horizons is not None else (row.horizon for row in returns)))
        )
        if not selected_horizons or any(horizon <= 0 for horizon in selected_horizons):
            raise ValueError("at least one positive horizon is required")

        points: list[FactorDecayPoint] = []
        for horizon in selected_horizons:
            series = self._ic.analyze_series(sections, returns, horizon)
            points.append(
                FactorDecayPoint(
                    horizon=horizon,
                    mean_ic=series.mean_ic,
                    mean_rank_ic=series.mean_rank_ic,
                    cross_sections=len(series.points),
                    observations=sum(point.observations for point in series.points),
                )
            )
        return FactorDecayProfile(sections[0].factor.name, tuple(points))
