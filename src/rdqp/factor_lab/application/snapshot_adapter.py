"""Adapters from platform analytics snapshots into Factor Lab observations."""

from __future__ import annotations

from collections.abc import Iterable

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.factor_lab.domain.models import FactorObservation


def observations_from_snapshots(
    snapshots: Iterable[FactorSnapshot],
) -> tuple[FactorObservation, ...]:
    """Map current analytics fields into stable Factor Lab names."""

    return tuple(
        FactorObservation(
            symbol=snapshot.symbol,
            timestamp=snapshot.timestamp,
            values={
                "momentum": snapshot.roc,
                "relative_volume": snapshot.rvol,
                "vwap_distance": snapshot.vwap_distance,
                "gap": snapshot.gap,
            },
        )
        for snapshot in snapshots
    )
