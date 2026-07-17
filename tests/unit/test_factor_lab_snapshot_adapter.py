from datetime import UTC, datetime

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.factor_lab import observations_from_snapshots


def test_snapshot_adapter_maps_supported_factor_names() -> None:
    snapshot = FactorSnapshot(
        "AAPL",
        datetime(2026, 1, 2, tzinfo=UTC),
        100.0,
        1_000.0,
        "Technology",
        0.02,
        1.5,
        99.0,
        0.01,
        0.03,
        101.0,
        98.0,
        "inside",
        1,
    )
    observation = observations_from_snapshots([snapshot])[0]
    assert observation.symbol == "AAPL"
    assert observation.values["momentum"] == 0.02
    assert observation.values["relative_volume"] == 1.5
