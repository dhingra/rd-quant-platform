from __future__ import annotations

from rdqp.execution.lifecycle.models import (
    OrderLifecycleEvent,
    OrderLifecycleRecord,
    OrderLifecycleState,
)

_ALLOWED: dict[OrderLifecycleState, set[OrderLifecycleState]] = {
    OrderLifecycleState.NEW: {
        OrderLifecycleState.SUBMITTED,
        OrderLifecycleState.REJECTED,
        OrderLifecycleState.CANCELLED,
    },
    OrderLifecycleState.SUBMITTED: {
        OrderLifecycleState.ACKNOWLEDGED,
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.FILLED,
        OrderLifecycleState.REJECTED,
        OrderLifecycleState.CANCELLED,
    },
    OrderLifecycleState.ACKNOWLEDGED: {
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.FILLED,
        OrderLifecycleState.REJECTED,
        OrderLifecycleState.CANCELLED,
    },
    OrderLifecycleState.PARTIALLY_FILLED: {
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.FILLED,
        OrderLifecycleState.CANCELLED,
    },
    OrderLifecycleState.FILLED: set(),
    OrderLifecycleState.CANCELLED: set(),
    OrderLifecycleState.REJECTED: set(),
}


class OrderLifecycleEngine:
    def apply(
        self, record: OrderLifecycleRecord, event: OrderLifecycleEvent
    ) -> OrderLifecycleRecord:
        if event.order_id != record.order_id:
            raise ValueError("event order_id does not match record")
        if any(existing.event_id == event.event_id for existing in record.events):
            return record
        if event.state not in _ALLOWED[record.state]:
            raise ValueError(f"invalid transition {record.state} -> {event.state}")
        quantity = record.filled_quantity + max(0, event.filled_quantity)
        average = record.average_fill_price
        if event.filled_quantity > 0 and event.fill_price is not None:
            previous_notional = record.filled_quantity * (record.average_fill_price or 0.0)
            average = (previous_notional + event.filled_quantity * event.fill_price) / quantity
        return OrderLifecycleRecord(
            record.order_id, event.state, quantity, average, record.events + (event,)
        )
