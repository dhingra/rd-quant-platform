from datetime import UTC, datetime

import pytest

from rdqp.factor_lab import (
    FactorDefinition,
    FactorNormalizer,
    FactorObservation,
    NormalizationMethod,
    percentile_ranks,
    winsorize,
    zscores,
)


def observations(values: list[float | None]) -> list[FactorObservation]:
    timestamp = datetime(2026, 1, 2, 15, 0, tzinfo=UTC)
    return [
        FactorObservation(f"S{index}", timestamp, {"momentum": value})
        for index, value in enumerate(values)
    ]


def test_winsorization_clips_outliers() -> None:
    result = winsorize([1.0, 2.0, 3.0, 100.0], 0.25, 0.75)
    assert result[0] == pytest.approx(1.75)
    assert result[-1] == pytest.approx(27.25)


def test_zscores_are_centered_and_constant_safe() -> None:
    result = zscores([1.0, 2.0, 3.0])
    assert sum(result) == pytest.approx(0.0)
    assert zscores([4.0, 4.0]) == (0.0, 0.0)


def test_percentile_ranks_are_tie_aware() -> None:
    assert percentile_ranks([10.0, 20.0, 20.0, 30.0]) == pytest.approx((0.0, 0.5, 0.5, 1.0))


def test_normalizer_ignores_missing_and_respects_direction() -> None:
    definition = FactorDefinition(
        "momentum",
        higher_is_better=False,
        winsor_lower=0.0,
        winsor_upper=1.0,
    )
    result = FactorNormalizer().normalize(
        definition,
        observations([1.0, 2.0, None, 3.0]),
        NormalizationMethod.PERCENTILE,
    )
    assert [row.symbol for row in result.scores] == ["S0", "S1", "S3"]
    assert [row.score for row in result.scores] == pytest.approx((0.0, -0.5, -1.0))
    assert [row.percentile for row in result.scores] == pytest.approx((1.0, 0.5, 0.0))


def test_normalizer_rejects_mixed_timestamps() -> None:
    rows = observations([1.0, 2.0])
    rows[1] = FactorObservation("S1", datetime(2026, 1, 3, tzinfo=UTC), {"momentum": 2.0})
    with pytest.raises(ValueError, match="one timestamp"):
        FactorNormalizer().normalize(FactorDefinition("momentum"), rows)
