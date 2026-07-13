"""Execution-domain ports."""

from abc import ABC, abstractmethod

from rdqp.market.domain.models import Order


class Broker(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def submit_order(self, order: Order) -> str: ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> None: ...
