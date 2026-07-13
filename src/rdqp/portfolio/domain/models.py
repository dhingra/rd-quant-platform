"""Paper-portfolio domain records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class PaperPosition:
    symbol: str
    quantity: int
    average_price: float
    last_price: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.last_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.last_price - self.average_price) * self.quantity


@dataclass(frozen=True, slots=True)
class JournalEntry:
    timestamp: datetime
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    realized_pnl: float
    note: str = ""


@dataclass(frozen=True, slots=True)
class PaperPortfolioSnapshot:
    initial_cash: float
    cash: float
    positions: tuple[PaperPosition, ...]
    journal: tuple[JournalEntry, ...]

    @property
    def market_value(self) -> float:
        return sum(position.market_value for position in self.positions)

    @property
    def equity(self) -> float:
        return self.cash + self.market_value

    @property
    def realized_pnl(self) -> float:
        return sum(entry.realized_pnl for entry in self.journal)

    @property
    def unrealized_pnl(self) -> float:
        return sum(position.unrealized_pnl for position in self.positions)
