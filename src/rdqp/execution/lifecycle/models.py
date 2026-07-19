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
    state: OrderLifecycleState = OrderLifecycleState.NEW
    filled_quantity: int = 0
    average_fill_price: float | None = None
    events: tuple[OrderLifecycleEvent, ...] = ()
