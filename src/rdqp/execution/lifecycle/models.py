from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from rdqp.execution.domain.models import utc_now


class OrderLifecycleState(StrEnum):
    NEW = "NEW"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class OrderLifecycleEvent:
    event_id: str
    order_id: str
    state: OrderLifecycleState
    filled_quantity: int = 0
    fill_price: float | None = None
    message: str = ""
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class OrderLifecycleRecord:
    order_id: str
    requested_quantity: int | None = None
    state: OrderLifecycleState = OrderLifecycleState.NEW
    filled_quantity: int = 0
    average_fill_price: float | None = None
    events: tuple[OrderLifecycleEvent, ...] = ()

    def __post_init__(self) -> None:
        if self.requested_quantity is not None and self.requested_quantity <= 0:
            raise ValueError("requested_quantity must be positive")
        if self.filled_quantity < 0:
            raise ValueError("filled_quantity cannot be negative")
        if (
            self.requested_quantity is not None
            and self.filled_quantity > self.requested_quantity
        ):
            raise ValueError("filled_quantity exceeds requested_quantity")

    @property
    def remaining_quantity(self) -> int | None:
        if self.requested_quantity is None:
            return None
        return self.requested_quantity - self.filled_quantity
