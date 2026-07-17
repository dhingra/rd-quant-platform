from datetime import UTC, datetime, timedelta

import pytest

from rdqp.factor_lab import (
    FactorCrossSection,
    FactorDecayAnalyzer,
    FactorDefinition,
    FactorResearchReportBuilder,
    FactorScore,
    ForwardReturnObservation,
    NormalizationMethod,
)


def make_section(timestamp: datetime) -> FactorCrossSection:
    values = (1.0, 2.0, 3.0, 4.0)
    return FactorCrossSection(
        FactorDefinition("momentum", winsor_lower=0.0, winsor_upper=1.0),
        timestamp,
        NormalizationMethod.RAW,
        tuple(
            FactorScore(f"S{i}", "momentum", value, value, value, i / 3)
            for i, value in enumerate(values)
        ),
    )


def test_decay_profile_orders_horizons_and_aggregates() -> None:
    timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    sections = [make_section(timestamp), make_section(timestamp + timedelta(days=1))]
    returns = [
        ForwardReturnObservation(f"S{i}", item.timestamp, horizon, value * scale)
        for item in sections
        for horizon, scale in ((1, 1.0), (5, 0.5))
        for i, value in enumerate((-0.02, 0.0, 0.01, 0.03))
    ]
    profile = FactorDecayAnalyzer().analyze(sections, returns, horizons=(5, 1))
    assert [point.horizon for point in profile.points] == [1, 5]
    assert all(point.mean_rank_ic == pytest.approx(1.0) for point in profile.points)
    assert all(point.observations == 8 for point in profile.points)


def test_report_builder_combines_ic_quantiles_and_decay() -> None:
    timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    sections = [make_section(timestamp)]
    returns = [
        ForwardReturnObservation(f"S{i}", timestamp, horizon, value)
        for horizon in (1, 5)
        for i, value in enumerate((-0.02, 0.0, 0.01, 0.03))
    ]
    report = FactorResearchReportBuilder().build(sections, returns, quantile_buckets=2)
    assert report.factor == "momentum"
    assert [series.horizon for series in report.ic_series] == [1, 5]
    assert len(report.quantile_analyses) == 1
    assert report.quantile_analyses[0].long_short_spread == pytest.approx(0.03)
