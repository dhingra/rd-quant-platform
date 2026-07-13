"""Execution-domain records shared by brokers, risk, and the terminal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


def utc_now() -> datetime:
    return datetime.now(UTC)


class ExecutionMode(StrEnum):
    PAPER = "PAPER"
    IBKR_PAPER = "IBKR_PAPER"


class ExecutionSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class ExecutionOrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class ExecutionStatus(StrEnum):
    PENDING_RISK = "PENDING_RISK"
    REJECTED = "REJECTED"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class OrderRequest:
    symbol: str
    side: ExecutionSide
    quantity: int
    order_type: ExecutionOrderType = ExecutionOrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    reference_price: float | None = None
    strategy: str = "manual"
    note: str = ""

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.order_type is ExecutionOrderType.LIMIT and not self.limit_price:
            raise ValueError("limit_price is required for LIMIT orders")
        if self.order_type is ExecutionOrderType.STOP and not self.stop_price:
            raise ValueError("stop_price is required for STOP orders")


@dataclass(frozen=True, slots=True)
class ManagedOrder:
    order_id: str
    request: OrderRequest
    mode: ExecutionMode
    status: ExecutionStatus
    broker_order_id: str | None = None
    submitted_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    filled_quantity: int = 0
    average_fill_price: float | None = None
    commission: float = 0.0
    message: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionFill:
    fill_id: str
    order_id: str
    broker_order_id: str | None
    symbol: str
    side: ExecutionSide
    quantity: int
    price: float
    commission: float
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class BrokerPosition:
    symbol: str
    quantity: float
    average_cost: float
    market_price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.market_price - self.average_cost) * self.quantity


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    account_id: str
    currency: str
    net_liquidation: float
    cash: float
    buying_power: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    positions: tuple[BrokerPosition, ...] = ()
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class ExecutionSnapshot:
    account: AccountSnapshot
    orders: tuple[ManagedOrder, ...]
    fills: tuple[ExecutionFill, ...]
