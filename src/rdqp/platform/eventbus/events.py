"""Domain events for the streaming pipeline."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from rdqp.market.domain.models import Order, Tick, Trade, utc_now


@dataclass(frozen=True, slots=True)
class Event:
    occurred_at: datetime = field(default_factory=utc_now, kw_only=True)


@dataclass(frozen=True, slots=True)
class TickReceived(Event):
    tick: Tick


@dataclass(frozen=True, slots=True)
class FactorUpdated(Event):
    symbol: str
    factors: Mapping[str, float | None]


@dataclass(frozen=True, slots=True)
class RankingUpdated(Event):
    rows: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class ScannerTriggered(Event):
    scanner: str
    symbol: str
    details: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class SignalGenerated(Event):
    signal_id: str
    symbol: str
    details: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class OrderSubmitted(Event):
    order: Order


@dataclass(frozen=True, slots=True)
class TradeFilled(Event):
    trade: Trade


@dataclass(frozen=True, slots=True)
class PortfolioUpdated(Event):
    equity: float
    cash: float
