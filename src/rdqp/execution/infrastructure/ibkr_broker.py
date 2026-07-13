"""Interactive Brokers paper-trading adapter.

The adapter refuses to connect unless ``paper_only`` is true and the configured
port is one of the standard paper ports. Live trading is intentionally outside
Sprint 5.
"""

from __future__ import annotations

from datetime import datetime, timezone

from rdqp.common.exceptions import ProviderUnavailableError
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


class IBKRPaperBroker(ExecutionBroker):
    PAPER_PORTS = {7497, 4002}

    def __init__(self, host: str, port: int, client_id: int, paper_only: bool = True) -> None:
        if not paper_only:
            raise ValueError("Sprint 5 supports IBKR paper execution only")
        if port not in self.PAPER_PORTS:
            raise ValueError("IBKR execution port must be a standard paper port: 7497 or 4002")
        self._host = host
        self._port = port
        self._client_id = client_id
        self._ib = None
        self._orders: dict[str, ManagedOrder] = {}
        self._fills: list[ExecutionFill] = []

    @property
    def name(self) -> str:
        return "ibkr-paper"

    def connect(self) -> None:
        try:
            from ib_insync import IB
        except ImportError as exc:
            raise ProviderUnavailableError("Install the 'ibkr' extra to use IBKR execution") from exc
        ib = IB()
        ib.connect(self._host, self._port, clientId=self._client_id, readonly=False, timeout=5)
        self._ib = ib

    def disconnect(self) -> None:
        if self._ib is not None:
            self._ib.disconnect()
            self._ib = None

    def _require_connection(self):
        if self._ib is None or not self._ib.isConnected():
            raise RuntimeError("IBKR paper broker is not connected")
        return self._ib

    def account_snapshot(self, prices: dict[str, float] | None = None) -> AccountSnapshot:
        ib = self._require_connection()
        values = {item.tag: item.value for item in ib.accountSummary()}
        positions: list[BrokerPosition] = []
        for item in ib.positions():
            market_price = (prices or {}).get(item.contract.symbol, float(item.avgCost))
            positions.append(
                BrokerPosition(
                    symbol=item.contract.symbol,
                    quantity=float(item.position),
                    average_cost=float(item.avgCost),
                    market_price=float(market_price),
                )
            )
        account_id = next(iter(ib.managedAccounts()), "IBKR-PAPER")
        return AccountSnapshot(
            account_id=account_id,
            currency="USD",
            net_liquidation=float(values.get("NetLiquidation", 0) or 0),
            cash=float(values.get("TotalCashValue", 0) or 0),
            buying_power=float(values.get("BuyingPower", 0) or 0),
            realized_pnl=float(values.get("RealizedPnL", 0) or 0),
            unrealized_pnl=float(values.get("UnrealizedPnL", 0) or 0),
            positions=tuple(positions),
        )

    def submit(self, order_id: str, request: OrderRequest) -> ManagedOrder:
        ib = self._require_connection()
        try:
            from ib_insync import LimitOrder, MarketOrder, Stock, StopOrder
        except ImportError as exc:  # pragma: no cover
            raise ProviderUnavailableError("Install ib-insync") from exc
        contract = Stock(request.symbol.upper(), "SMART", "USD")
        ib.qualifyContracts(contract)
        action = request.side.value
        if request.order_type is ExecutionOrderType.MARKET:
            ib_order = MarketOrder(action, request.quantity)
        elif request.order_type is ExecutionOrderType.LIMIT:
            ib_order = LimitOrder(action, request.quantity, request.limit_price)
        else:
            ib_order = StopOrder(action, request.quantity, request.stop_price)
        trade = ib.placeOrder(contract, ib_order)
        ib.sleep(0.25)
        status_text = str(trade.orderStatus.status or "Submitted")
        status = self._map_status(status_text)
        broker_order_id = str(trade.order.orderId)
        average_fill = float(trade.orderStatus.avgFillPrice or 0) or None
        filled_quantity = int(trade.orderStatus.filled or 0)
        managed = ManagedOrder(
            order_id=order_id,
            request=request,
            mode=ExecutionMode.IBKR_PAPER,
            status=status,
            broker_order_id=broker_order_id,
            filled_quantity=filled_quantity,
            average_fill_price=average_fill,
            message=f"IBKR status: {status_text}",
        )
        self._orders[order_id] = managed
        for fill in trade.fills:
            execution = fill.execution
            self._fills.append(
                ExecutionFill(
                    fill_id=str(execution.execId),
                    order_id=order_id,
                    broker_order_id=broker_order_id,
                    symbol=request.symbol.upper(),
                    side=request.side,
                    quantity=int(execution.shares),
                    price=float(execution.price),
                    commission=float(getattr(fill.commissionReport, "commission", 0) or 0),
                    timestamp=execution.time if execution.time.tzinfo else execution.time.replace(tzinfo=timezone.utc),
                )
            )
        return managed

    def cancel(self, broker_order_id: str) -> None:
        ib = self._require_connection()
        for trade in ib.openTrades():
            if str(trade.order.orderId) == str(broker_order_id):
                ib.cancelOrder(trade.order)
                return
        raise ValueError(f"Open IBKR order not found: {broker_order_id}")

    def open_orders(self) -> tuple[ManagedOrder, ...]:
        if self._ib is None or not self._ib.isConnected():
            return ()
        open_ids = {str(trade.order.orderId) for trade in self._ib.openTrades()}
        return tuple(order for order in self._orders.values() if order.broker_order_id in open_ids)

    def fills(self) -> tuple[ExecutionFill, ...]:
        return tuple(self._fills)

    @staticmethod
    def _map_status(status: str) -> ExecutionStatus:
        normalized = status.lower()
        if normalized == "filled":
            return ExecutionStatus.FILLED
        if normalized in {"cancelled", "apicancelled"}:
            return ExecutionStatus.CANCELLED
        if normalized in {"inactive"}:
            return ExecutionStatus.REJECTED
        if normalized in {"presubmitted", "submitted", "pendingsubmit"}:
            return ExecutionStatus.SUBMITTED
        return ExecutionStatus.SUBMITTED
