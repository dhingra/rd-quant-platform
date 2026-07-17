"""IBKR paper-account reader used by :class:`AccountSyncService`."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from rdqp.common.exceptions import ProviderUnavailableError
from rdqp.execution.account_sync.models import BrokerAccountState
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
    utc_now,
)


class IBKRAccountReader:
    PAPER_PORTS = {7497, 4002}

    def __init__(self, host: str, port: int, client_id: int, *, paper_only: bool = True) -> None:
        if not paper_only:
            raise ValueError("IBKR account synchronization is paper-only")
        if port not in self.PAPER_PORTS:
            raise ValueError("IBKR paper port must be 7497 or 4002")
        self._host = host
        self._port = port
        self._client_id = client_id
        self._ib: Any | None = None

    @property
    def name(self) -> str:
        return "ibkr-paper"

    def connect(self, *, readonly: bool = True, timeout: float = 5.0) -> None:
        try:
            from ib_insync import IB
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Install the 'ibkr' extra to use IBKR account synchronization"
            ) from exc
        ib = IB()  # type: ignore[no-untyped-call]
        ib.connect(
            self._host,
            self._port,
            clientId=self._client_id,
            readonly=readonly,
            timeout=timeout,
        )
        self._ib = ib

    def disconnect(self) -> None:
        if self._ib is not None:
            self._ib.disconnect()
            self._ib = None

    def is_connected(self) -> bool:
        return self._ib is not None and bool(self._ib.isConnected())

    def read_account_state(self) -> BrokerAccountState:
        ib = self._require_connection()
        synchronized_at = utc_now()
        account_id = next(iter(ib.managedAccounts()), "IBKR-PAPER")
        summary = self._account_summary(ib)
        positions = self._positions(ib)
        orders = self._open_orders(ib)
        executions = self._executions(ib)

        account = AccountSnapshot(
            account_id=account_id,
            currency=summary.get("Currency", "USD"),
            net_liquidation=self._number(summary.get("NetLiquidation")),
            cash=self._number(summary.get("TotalCashValue")),
            buying_power=self._number(summary.get("BuyingPower")),
            realized_pnl=self._number(summary.get("RealizedPnL")),
            unrealized_pnl=self._number(summary.get("UnrealizedPnL")),
            positions=positions,
            timestamp=synchronized_at,
        )
        return BrokerAccountState(
            account=account,
            open_orders=orders,
            executions=executions,
            synchronized_at=synchronized_at,
            source=self.name,
        )

    def _require_connection(self) -> Any:
        if not self.is_connected():
            raise RuntimeError("IBKR paper account reader is not connected")
        return self._ib

    @staticmethod
    def _account_summary(ib: Any) -> dict[str, str]:
        return {str(item.tag): str(item.value) for item in ib.accountSummary()}

    @classmethod
    def _positions(cls, ib: Any) -> tuple[BrokerPosition, ...]:
        results: list[BrokerPosition] = []
        tickers = {ticker.contract.conId: ticker for ticker in ib.tickers()}
        for item in ib.positions():
            ticker = tickers.get(item.contract.conId)
            market_price = cls._market_price(ticker, float(item.avgCost))
            results.append(
                BrokerPosition(
                    symbol=str(item.contract.symbol),
                    quantity=float(item.position),
                    average_cost=float(item.avgCost),
                    market_price=market_price,
                )
            )
        return tuple(sorted(results, key=lambda position: position.symbol))

    @classmethod
    def _open_orders(cls, ib: Any) -> tuple[ManagedOrder, ...]:
        orders: list[ManagedOrder] = []
        for trade in ib.openTrades():
            side = cls._side(str(trade.order.action))
            order_type = cls._order_type(str(trade.order.orderType))
            quantity = int(trade.order.totalQuantity)
            request = OrderRequest(
                symbol=str(trade.contract.symbol),
                side=side,
                quantity=quantity,
                order_type=order_type,
                limit_price=cls._optional_number(getattr(trade.order, "lmtPrice", None)),
                stop_price=cls._optional_number(getattr(trade.order, "auxPrice", None)),
                strategy="ibkr-sync",
            )
            orders.append(
                ManagedOrder(
                    order_id=f"IBKR-{trade.order.orderId}",
                    request=request,
                    mode=ExecutionMode.IBKR_PAPER,
                    status=cls._status(str(trade.orderStatus.status)),
                    broker_order_id=str(trade.order.orderId),
                    filled_quantity=int(trade.orderStatus.filled or 0),
                    average_fill_price=cls._optional_number(trade.orderStatus.avgFillPrice),
                    message="Synchronized from IBKR",
                )
            )
        return tuple(orders)

    @classmethod
    def _executions(cls, ib: Any) -> tuple[ExecutionFill, ...]:
        fills: list[ExecutionFill] = []
        for fill in ib.fills():
            execution = fill.execution
            timestamp = execution.time
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            fills.append(
                ExecutionFill(
                    fill_id=str(execution.execId),
                    order_id=f"IBKR-{execution.orderId}",
                    broker_order_id=str(execution.orderId),
                    symbol=str(fill.contract.symbol),
                    side=cls._side(str(execution.side)),
                    quantity=int(execution.shares),
                    price=float(execution.price),
                    commission=cls._number(getattr(fill.commissionReport, "commission", 0.0)),
                    timestamp=timestamp,
                )
            )
        return tuple(fills)

    @staticmethod
    def _market_price(ticker: Any | None, fallback: float) -> float:
        if ticker is None:
            return fallback
        price = ticker.marketPrice()
        if price is None or price != price or price <= 0:
            return fallback
        return float(price)

    @staticmethod
    def _number(value: object | None) -> float:
        raw: Any = 0.0 if value is None else value
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _optional_number(cls, value: object | None) -> float | None:
        number = cls._number(value)
        return number if number > 0 else None

    @staticmethod
    def _side(value: str) -> ExecutionSide:
        normalized = value.upper()
        if normalized in {"BUY", "BOT"}:
            return ExecutionSide.BUY
        if normalized in {"SELL", "SLD"}:
            return ExecutionSide.SELL
        raise ValueError(f"Unsupported IBKR execution side: {value}")

    @staticmethod
    def _order_type(value: str) -> ExecutionOrderType:
        normalized = value.upper()
        if normalized in {"LMT", "LIMIT"}:
            return ExecutionOrderType.LIMIT
        if normalized in {"STP", "STOP"}:
            return ExecutionOrderType.STOP
        return ExecutionOrderType.MARKET

    @staticmethod
    def _status(value: str) -> ExecutionStatus:
        normalized = value.lower()
        if normalized == "filled":
            return ExecutionStatus.FILLED
        if normalized in {"cancelled", "apicancelled"}:
            return ExecutionStatus.CANCELLED
        if normalized == "inactive":
            return ExecutionStatus.REJECTED
        if normalized == "partiallyfilled":
            return ExecutionStatus.PARTIALLY_FILLED
        return ExecutionStatus.SUBMITTED
