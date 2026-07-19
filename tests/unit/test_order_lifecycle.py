import pytest

from rdqp.execution import (
    OrderLifecycleEngine,
    OrderLifecycleEvent,
    OrderLifecycleRecord,
    OrderLifecycleState,
)


def test_lifecycle_is_idempotent_and_aggregates_fills() -> None:
    engine = OrderLifecycleEngine()
    record = OrderLifecycleRecord("o1")
    record = engine.apply(record, OrderLifecycleEvent("e1", "o1", OrderLifecycleState.SUBMITTED))
    record = engine.apply(
        record, OrderLifecycleEvent("e2", "o1", OrderLifecycleState.PARTIALLY_FILLED, 2, 100.0)
    )
    record = engine.apply(
        record, OrderLifecycleEvent("e3", "o1", OrderLifecycleState.FILLED, 3, 110.0)
    )
    assert record.filled_quantity == 5
    assert record.average_fill_price == 106.0
    assert engine.apply(record, record.events[-1]) is record


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(ValueError):
        OrderLifecycleEngine().apply(
            OrderLifecycleRecord("o1"), OrderLifecycleEvent("e", "o1", OrderLifecycleState.FILLED)
        )
