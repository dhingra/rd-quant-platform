"""Deterministic in-process broker used to validate execution and risk workflows."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from rdqp.execution.domain.models import (
    AccountSnapshot,
    BrokerPosition,
    ExecutionFill,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionSide,
    ExecutionStatus,
    ManagedOrder,
    OrderRequest,
)
from rdqp.execution.domain.ports import ExecutionBroker


class PaperExecutionBroker(ExecutionBroker):
    def __init__(self, initial_cash: float = 100_000.0, commission_per_order: float = 0.0) -> None:
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._commission = commission_per_order
        self._connected = False
        self._positions: dict[str, BrokerPosition] = {}
        self._orders: dict[str, ManagedOrder] = {}
        self._fills: list[ExecutionFill] = []
        self._realized_pnl = 0.0

    @property
    def name(self) -> str:
        return "paper"

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def account_snapshot(self, prices: dict[str, float] | None = None) -> AccountSnapshot:
        prices = prices or {}
        for symbol, position in list(self._positions.items()):
            price = prices.get(symbol, position.market_price)
            self._positions[symbol] = replace(position, market_price=price)
        positions = tuple(sorted(self._positions.values(), key=lambda p: p.symbol))
        unrealized = sum(position.unrealized_pnl for position in positions)
        market_value = sum(position.market_value for position in positions)
        equity = self._cash + market_value
        return AccountSnapshot(
            account_id="RDQP-PAPER",
            currency="USD",
            net_liquidation=equity,
            cash=self._cash,
            buying_power=max(0.0, self._cash),
            realized_pnl=self._realized_pnl,
            unrealized_pnl=unrealized,
            positions=positions,
        )

    def submit(self, order_id: str, request: OrderRequest) -> ManagedOrder:
        if not self._connected:
            raise RuntimeError("Paper broker is not connected")
        price = request.reference_price
        if request.order_type is ExecutionOrderType.LIMIT:
            price = request.limit_price
        elif request.order_type is ExecutionOrderType.STOP:
            price = request.stop_price
        if price is None or price <= 0:
            raise ValueError("A fill price is required for paper execution")
        symbol = request.symbol.upper()
        current = self._positions.get(symbol)
        now = datetime.now(UTC)
        if request.side is ExecutionSide.BUY:
            cost = price * request.quantity + self._commission
            if cost > self._cash:
                raise ValueError("Insufficient paper cash")
            old_qty = 0.0 if current is None else current.quantity
            old_cost = 0.0 if current is None else current.average_cost * current.quantity
            new_qty = old_qty + request.quantity
            average = (old_cost + price * request.quantity) / new_qty
            self._positions[symbol] = BrokerPosition(symbol, new_qty, average, price)
            self._cash -= cost
        else:
            if current is None or current.quantity < request.quantity:
                raise ValueError("Insufficient paper position")
            self._realized_pnl += (
                price - current.average_cost
            ) * request.quantity - self._commission
            remaining = current.quantity - request.quantity
            self._cash += price * request.quantity - self._commission
            if remaining:
                self._positions[symbol] = BrokerPosition(
                    symbol, remaining, current.average_cost, price
                )
            else:
                del self._positions[symbol]
        broker_order_id = f"PAPER-{uuid4().hex[:12]}"
        order = ManagedOrder(
            order_id=order_id,
            request=request,
            mode=ExecutionMode.PAPER,
            status=ExecutionStatus.FILLED,
            broker_order_id=broker_order_id,
            submitted_at=now,
            updated_at=now,
            filled_quantity=request.quantity,
            average_fill_price=price,
            commission=self._commission,
            message="Filled by local paper broker",
        )
        fill = ExecutionFill(
            fill_id=f"FILL-{uuid4().hex[:12]}",
            order_id=order_id,
            broker_order_id=broker_order_id,
            symbol=symbol,
            side=request.side,
            quantity=request.quantity,
            price=price,
            commission=self._commission,
            timestamp=now,
        )
        self._orders[order_id] = order
        self._fills.append(fill)
        return order

    def cancel(self, broker_order_id: str) -> None:
        for key, order in self._orders.items():
            if (
                order.broker_order_id == broker_order_id
                and order.status is ExecutionStatus.SUBMITTED
            ):
                self._orders[key] = replace(order, status=ExecutionStatus.CANCELLED)
                return

    def open_orders(self) -> tuple[ManagedOrder, ...]:
        return tuple(
            order
            for order in self._orders.values()
            if order.status in {ExecutionStatus.SUBMITTED, ExecutionStatus.PARTIALLY_FILLED}
        )

    def fills(self) -> tuple[ExecutionFill, ...]:
        return tuple(self._fills)
