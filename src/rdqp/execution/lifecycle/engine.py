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
        if event.filled_quantity < 0:
            raise ValueError("filled quantity cannot be negative")
        if event.filled_quantity > 0 and event.fill_price is None:
            raise ValueError("fill_price is required when filled_quantity is positive")
        if event.fill_price is not None and event.fill_price <= 0:
            raise ValueError("fill_price must be positive")

        quantity = record.filled_quantity + event.filled_quantity
        if record.requested_quantity is not None:
            if quantity > record.requested_quantity:
                raise ValueError("fill exceeds requested quantity")
            if event.state is OrderLifecycleState.FILLED and quantity != record.requested_quantity:
                raise ValueError("FILLED event must complete requested quantity")
            if (
                event.state is OrderLifecycleState.PARTIALLY_FILLED
                and quantity >= record.requested_quantity
            ):
                raise ValueError("PARTIALLY_FILLED event cannot complete the order")
        if event.state is OrderLifecycleState.FILLED and quantity <= 0:
            raise ValueError("FILLED event requires a positive cumulative fill")

        average = record.average_fill_price
        if event.filled_quantity > 0:
            assert event.fill_price is not None
            previous_notional = record.filled_quantity * (record.average_fill_price or 0.0)
            average = (
                previous_notional + event.filled_quantity * event.fill_price
            ) / quantity

        return OrderLifecycleRecord(
            order_id=record.order_id,
            requested_quantity=record.requested_quantity,
            state=event.state,
            filled_quantity=quantity,
            average_fill_price=average,
            events=record.events + (event,),
        )
