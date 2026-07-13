"""Immutable market-domain models."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(StrEnum):
    NEW = "NEW"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Tick:
    symbol: str
    timestamp: datetime
    price: float
    size: float = 0.0
    source: str = "unknown"

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")


@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: float = 0.0
    ask_size: float = 0.0
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class Signal:
    symbol: str
    timestamp: datetime
    side: Side
    strength: float
    strategy: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Order:
    order_id: str
    symbol: str
    side: Side
    quantity: float
    order_type: OrderType
    status: OrderStatus = OrderStatus.NEW
    limit_price: float | None = None
    stop_price: float | None = None
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class Trade:
    trade_id: str
    order_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0


@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    quantity: float
    average_price: float
    market_price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price

    @property
    def unrealized_pnl(self) -> float:
        return self.quantity * (self.market_price - self.average_price)


@dataclass(frozen=True, slots=True)
class Portfolio:
    cash: float
    positions: tuple[Position, ...] = ()

    @property
    def equity(self) -> float:
        return self.cash + sum(position.market_value for position in self.positions)
