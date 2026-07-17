from datetime import UTC, datetime

import pytest

from rdqp.factor_lab import (
    FactorCorrelationAnalyzer,
    FactorObservation,
    pearson_correlation,
)


def test_pearson_correlation_handles_perfect_and_constant_series() -> None:
    assert pearson_correlation([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)
    assert pearson_correlation([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]) == pytest.approx(-1.0)
    assert pearson_correlation([1.0, 1.0], [2.0, 3.0]) is None


def test_correlation_analyzer_uses_pairwise_complete_observations() -> None:
    timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    rows = [
        FactorObservation("A", timestamp, {"momentum": 1.0, "value": 3.0}),
        FactorObservation("B", timestamp, {"momentum": 2.0, "value": 2.0}),
        FactorObservation("C", timestamp, {"momentum": 3.0, "value": 1.0}),
        FactorObservation("D", timestamp, {"momentum": 4.0, "value": None}),
    ]
    matrix = FactorCorrelationAnalyzer().analyze(rows, ("momentum", "value"))
    cell = next(item for item in matrix.cells if item.left == "momentum" and item.right == "value")
    assert cell.observations == 3
    assert cell.correlation == pytest.approx(-1.0)
