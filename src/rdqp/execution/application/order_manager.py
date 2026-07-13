"""Order orchestration: pre-trade risk, broker submission, and durable journal."""

from __future__ import annotations

from uuid import uuid4

from rdqp.execution.domain.models import (
    ExecutionMode,
    ExecutionStatus,
    ManagedOrder,
    OrderRequest,
)
from rdqp.execution.domain.ports import ExecutionBroker, TradeJournal
from rdqp.risk import RiskEngine, RiskLimits


class OrderManager:
    def __init__(
        self,
        broker: ExecutionBroker,
        journal: TradeJournal,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self._broker = broker
        self._journal = journal
        self._risk_engine = risk_engine or RiskEngine()

    @property
    def broker(self) -> ExecutionBroker:
        return self._broker

    def submit(
        self,
        request: OrderRequest,
        limits: RiskLimits,
        prices: dict[str, float] | None = None,
    ) -> ManagedOrder:
        account = self._broker.account_snapshot(prices)
        decision = self._risk_engine.evaluate(
            request,
            account,
            limits,
            len(self._broker.open_orders()),
        )
        order_id = f"RDQP-{uuid4().hex[:14]}"
        if not decision.approved:
            rejected = ManagedOrder(
                order_id=order_id,
                request=request,
                mode=ExecutionMode.PAPER
                if self._broker.name == "paper"
                else ExecutionMode.IBKR_PAPER,
                status=ExecutionStatus.REJECTED,
                message=decision.reason,
            )
            self._journal.record_order(rejected)
            return rejected
        try:
            order = self._broker.submit(order_id, request)
        except Exception as exc:
            order = ManagedOrder(
                order_id=order_id,
                request=request,
                mode=ExecutionMode.PAPER
                if self._broker.name == "paper"
                else ExecutionMode.IBKR_PAPER,
                status=ExecutionStatus.ERROR,
                message=str(exc),
            )
        self._journal.record_order(order)
        for fill in self._broker.fills():
            if fill.order_id == order_id:
                self._journal.record_fill(fill)
        return order

    def cancel(self, broker_order_id: str) -> None:
        self._broker.cancel(broker_order_id)

    def recent_orders(self, limit: int = 100) -> tuple[ManagedOrder, ...]:
        return self._journal.recent_orders(limit)
