"""In-memory paper portfolio used by Strategy Lab."""

from __future__ import annotations

from datetime import datetime, timezone

from rdqp.portfolio.domain.models import (
    JournalEntry,
    OrderSide,
    PaperPortfolioSnapshot,
    PaperPosition,
)


class PaperPortfolio:
    def __init__(self, initial_cash: float = 100_000.0) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self._positions: dict[str, PaperPosition] = {}
        self._journal: list[JournalEntry] = []

    def buy(self, symbol: str, quantity: int, price: float, note: str = "") -> JournalEntry:
        self._validate(quantity, price)
        cost = quantity * price
        if cost > self.cash:
            raise ValueError("Insufficient paper cash")
        symbol = symbol.upper()
        current = self._positions.get(symbol)
        old_qty = 0 if current is None else current.quantity
        old_cost = 0.0 if current is None else current.average_price * current.quantity
        new_qty = old_qty + quantity
        average = (old_cost + cost) / new_qty
        self.cash -= cost
        self._positions[symbol] = PaperPosition(symbol, new_qty, average, price)
        entry = JournalEntry(
            datetime.now(timezone.utc), symbol, OrderSide.BUY, quantity, price, 0.0, note
        )
        self._journal.append(entry)
        return entry

    def sell(self, symbol: str, quantity: int, price: float, note: str = "") -> JournalEntry:
        self._validate(quantity, price)
        symbol = symbol.upper()
        current = self._positions.get(symbol)
        if current is None or quantity > current.quantity:
            raise ValueError("Insufficient paper position")
        realized = (price - current.average_price) * quantity
        remaining = current.quantity - quantity
        self.cash += quantity * price
        if remaining:
            self._positions[symbol] = PaperPosition(symbol, remaining, current.average_price, price)
        else:
            del self._positions[symbol]
        entry = JournalEntry(
            datetime.now(timezone.utc), symbol, OrderSide.SELL, quantity, price, realized, note
        )
        self._journal.append(entry)
        return entry

    def mark(self, prices: dict[str, float]) -> None:
        for symbol, current in list(self._positions.items()):
            if symbol in prices:
                self._positions[symbol] = PaperPosition(
                    symbol, current.quantity, current.average_price, prices[symbol]
                )

    def snapshot(self) -> PaperPortfolioSnapshot:
        return PaperPortfolioSnapshot(
            self.initial_cash,
            self.cash,
            tuple(sorted(self._positions.values(), key=lambda item: item.symbol)),
            tuple(self._journal),
        )

    @staticmethod
    def _validate(quantity: int, price: float) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if price <= 0:
            raise ValueError("price must be positive")
