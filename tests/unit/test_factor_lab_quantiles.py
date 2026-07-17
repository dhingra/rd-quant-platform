from datetime import UTC, datetime

import pytest

from rdqp.factor_lab import (
    FactorCrossSection,
    FactorDefinition,
    FactorScore,
    NormalizationMethod,
    QuantileReturnAnalyzer,
)


def test_quantile_analysis_calculates_long_short_spread() -> None:
    timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    cross_section = FactorCrossSection(
        FactorDefinition("momentum", winsor_lower=0.0, winsor_upper=1.0),
        timestamp,
        NormalizationMethod.RAW,
        tuple(
            FactorScore(f"S{i}", "momentum", float(i), float(i), float(i), i / 9)
            for i in range(10)
        ),
    )
    returns = {f"S{i}": i / 100 for i in range(10)}
    result = QuantileReturnAnalyzer().analyze(cross_section, returns, buckets=5)
    assert [bucket.observations for bucket in result.buckets] == [2, 2, 2, 2, 2]
    assert result.buckets[0].mean_return == pytest.approx(0.005)
    assert result.buckets[-1].mean_return == pytest.approx(0.085)
    assert result.long_short_spread == pytest.approx(0.08)
    assert result.monotonicity == pytest.approx(1.0)


def test_quantile_analysis_supports_sparse_cross_sections() -> None:
    timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    cross_section = FactorCrossSection(
        FactorDefinition("value"),
        timestamp,
        NormalizationMethod.RAW,
        (FactorScore("A", "value", 1, 1, 1, 0.0),),
    )
    result = QuantileReturnAnalyzer().analyze(cross_section, {"A": 0.02}, buckets=5)
    assert sum(bucket.observations for bucket in result.buckets) == 1
    assert result.long_short_spread is None
