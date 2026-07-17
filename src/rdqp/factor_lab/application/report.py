"""Composable factor research report builder."""

from __future__ import annotations

from collections.abc import Iterable

from rdqp.factor_lab.application.decay import FactorDecayAnalyzer
from rdqp.factor_lab.application.information_coefficient import InformationCoefficientAnalyzer
from rdqp.factor_lab.application.quantiles import QuantileReturnAnalyzer
from rdqp.factor_lab.domain.information import FactorResearchReport, ForwardReturnObservation
from rdqp.factor_lab.domain.models import FactorCrossSection


class FactorResearchReportBuilder:
    """Build a deterministic report from normalized factor cross-sections."""

    def __init__(self) -> None:
        self._ic = InformationCoefficientAnalyzer()
        self._quantiles = QuantileReturnAnalyzer()
        self._decay = FactorDecayAnalyzer()

    def build(
        self,
        cross_sections: Iterable[FactorCrossSection],
        forward_returns: Iterable[ForwardReturnObservation],
        horizons: Iterable[int] | None = None,
        quantile_buckets: int = 5,
    ) -> FactorResearchReport:
        sections = tuple(cross_sections)
        returns = tuple(forward_returns)
        if not sections:
            raise ValueError("at least one cross-section is required")
        selected_horizons = tuple(
            sorted(set(horizons if horizons is not None else (row.horizon for row in returns)))
        )
        if not selected_horizons:
            raise ValueError("at least one forward-return horizon is required")
        ic_series = tuple(
            self._ic.analyze_series(sections, returns, horizon)
            for horizon in selected_horizons
        )
        primary_horizon = selected_horizons[0] if selected_horizons else 1
        return_map = {
            (row.timestamp, row.symbol): row.return_value
            for row in returns
            if row.horizon == primary_horizon
        }
        quantiles = tuple(
            self._quantiles.analyze(
                section,
                {
                    score.symbol: return_map[(section.timestamp, score.symbol)]
                    for score in section.scores
                    if (section.timestamp, score.symbol) in return_map
                },
                buckets=quantile_buckets,
                horizon=primary_horizon,
            )
            for section in sections
        )
        decay = self._decay.analyze(sections, returns, selected_horizons)
        return FactorResearchReport(
            factor=sections[0].factor.name,
            ic_series=ic_series,
            quantile_analyses=quantiles,
            decay=decay,
        )
