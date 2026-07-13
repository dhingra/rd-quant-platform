"""Pure cross-sectional market analytics."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from statistics import mean, median, pstdev

from rdqp.analytics.domain.models import FactorSnapshot


@dataclass(frozen=True, slots=True)
class MarketStatistics:
    count: int
    mean_roc: float | None
    median_roc: float | None
    standard_deviation: float | None
    skew: float | None
    positive_percentage: float | None
    advancers: int
    decliners: int
    unchanged: int
    above_vwap: int


def market_statistics(records: list[FactorSnapshot]) -> MarketStatistics:
    values = [r.roc for r in records if r.roc is not None and math.isfinite(r.roc)]
    if not values:
        return MarketStatistics(0, None, None, None, None, None, 0, 0, 0, 0)
    avg = mean(values)
    std = pstdev(values) if len(values) > 1 else 0.0
    skew = None
    if len(values) > 2 and std > 0:
        skew = sum(((value - avg) / std) ** 3 for value in values) / len(values)
    return MarketStatistics(
        count=len(values),
        mean_roc=avg,
        median_roc=median(values),
        standard_deviation=std,
        skew=skew,
        positive_percentage=sum(value > 0 for value in values) / len(values),
        advancers=sum(value > 0 for value in values),
        decliners=sum(value < 0 for value in values),
        unchanged=sum(value == 0 for value in values),
        above_vwap=sum((r.vwap_distance or 0) > 0 for r in records),
    )


def sector_strength(records: list[FactorSnapshot]) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if record.roc is not None:
            grouped[record.sector].append(record.roc)
    return sorted(
        (
            {"sector": sector, "average_roc": mean(values), "symbols": len(values)}
            for sector, values in grouped.items()
        ),
        key=lambda row: float(row["average_roc"]),
        reverse=True,
    )
