"""Analytics records exposed to dashboard and scanner consumers."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FactorSnapshot:
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    sector: str
    roc: float | None
    rvol: float | None
    vwap: float | None
    vwap_distance: float | None
    gap: float | None
    opening_range_high: float | None
    opening_range_low: float | None
    opening_range_state: str
    rank: int | None = None
