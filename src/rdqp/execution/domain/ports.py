"""Execution ports used by the application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rdqp.execution.domain.models import AccountSnapshot, ExecutionFill, ManagedOrder, OrderRequest


class ExecutionBroker(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def account_snapshot(self, prices: dict[str, float] | None = None) -> AccountSnapshot: ...

    @abstractmethod
    def submit(self, order_id: str, request: OrderRequest) -> ManagedOrder: ...

    @abstractmethod
    def cancel(self, broker_order_id: str) -> None: ...

    @abstractmethod
    def open_orders(self) -> tuple[ManagedOrder, ...]: ...

    @abstractmethod
    def fills(self) -> tuple[ExecutionFill, ...]: ...


class TradeJournal(ABC):
    @abstractmethod
    def record_order(self, order: ManagedOrder) -> None: ...

    @abstractmethod
    def record_fill(self, fill: ExecutionFill) -> None: ...

    @abstractmethod
    def recent_orders(self, limit: int = 100) -> tuple[ManagedOrder, ...]: ...

    @abstractmethod
    def recent_fills(self, limit: int = 100) -> tuple[ExecutionFill, ...]: ...
