from datetime import UTC, datetime, timedelta

import pytest

from rdqp.factor_lab import (
    FactorCrossSection,
    FactorDefinition,
    FactorScore,
    ForwardReturnObservation,
    InformationCoefficientAnalyzer,
    NormalizationMethod,
    average_ranks,
    spearman_correlation,
)


def section(timestamp: datetime, values: list[float]) -> FactorCrossSection:
    return FactorCrossSection(
        factor=FactorDefinition("momentum", winsor_lower=0.0, winsor_upper=1.0),
        timestamp=timestamp,
        method=NormalizationMethod.RAW,
        scores=tuple(
            FactorScore(f"S{index}", "momentum", value, value, value, index / 3)
            for index, value in enumerate(values)
        ),
    )


def test_average_ranks_and_spearman_are_tie_aware() -> None:
    assert average_ranks([10.0, 20.0, 20.0, 30.0]) == (1.0, 2.5, 2.5, 4.0)
    assert spearman_correlation([1.0, 2.0, 3.0], [10.0, 20.0, 30.0]) == pytest.approx(1.0)


def test_information_coefficient_point_matches_forward_returns() -> None:
    timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    result = InformationCoefficientAnalyzer().analyze_point(
        section(timestamp, [1.0, 2.0, 3.0, 4.0]),
        {"S0": -0.02, "S1": 0.0, "S2": 0.01, "S3": 0.03},
    )
    assert result.observations == 4
    assert result.ic is not None and result.ic > 0.95
    assert result.rank_ic == pytest.approx(1.0)


def test_information_coefficient_series_aggregates_points() -> None:
    start = datetime(2026, 1, 2, tzinfo=UTC)
    sections = [
        section(start, [1.0, 2.0, 3.0, 4.0]),
        section(start + timedelta(days=1), [4.0, 3.0, 2.0, 1.0]),
    ]
    returns = [
        ForwardReturnObservation(f"S{i}", item.timestamp, 1, value)
        for item in sections
        for i, value in enumerate([-0.02, 0.0, 0.01, 0.03])
    ]
    result = InformationCoefficientAnalyzer().analyze_series(sections, returns)
    assert len(result.points) == 2
    assert result.mean_rank_ic == pytest.approx(0.0)
    assert result.rank_ic_hit_rate == pytest.approx(0.5)
