import pytest

from rdqp.execution import (
    OrderLifecycleEngine,
    OrderLifecycleEvent,
    OrderLifecycleRecord,
    OrderLifecycleState,
)


def test_lifecycle_is_idempotent_and_aggregates_fills() -> None:
    engine = OrderLifecycleEngine()
    record = OrderLifecycleRecord("o1", requested_quantity=5)
    record = engine.apply(record, OrderLifecycleEvent("e1", "o1", OrderLifecycleState.SUBMITTED))
    record = engine.apply(
        record,
        OrderLifecycleEvent("e2", "o1", OrderLifecycleState.PARTIALLY_FILLED, 2, 100.0),
    )
    record = engine.apply(
        record,
        OrderLifecycleEvent("e3", "o1", OrderLifecycleState.FILLED, 3, 110.0),
    )
    assert record.filled_quantity == 5
    assert record.remaining_quantity == 0
    assert record.average_fill_price == 106.0
    assert engine.apply(record, record.events[-1]) is record


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(ValueError):
        OrderLifecycleEngine().apply(
            OrderLifecycleRecord("o1", requested_quantity=1),
            OrderLifecycleEvent("e", "o1", OrderLifecycleState.FILLED, 1, 10.0),
        )


def test_lifecycle_rejects_overfill_and_invalid_partial_completion() -> None:
    engine = OrderLifecycleEngine()
    submitted = engine.apply(
        OrderLifecycleRecord("o1", requested_quantity=5),
        OrderLifecycleEvent("e1", "o1", OrderLifecycleState.SUBMITTED),
    )
    with pytest.raises(ValueError, match="exceeds"):
        engine.apply(
            submitted,
            OrderLifecycleEvent("e2", "o1", OrderLifecycleState.FILLED, 6, 10.0),
        )
    with pytest.raises(ValueError, match="cannot complete"):
        engine.apply(
            submitted,
            OrderLifecycleEvent("e3", "o1", OrderLifecycleState.PARTIALLY_FILLED, 5, 10.0),
        )


def test_lifecycle_requires_valid_fill_data() -> None:
    engine = OrderLifecycleEngine()
    submitted = engine.apply(
        OrderLifecycleRecord("o1", requested_quantity=5),
        OrderLifecycleEvent("e1", "o1", OrderLifecycleState.SUBMITTED),
    )
    with pytest.raises(ValueError, match="cannot be negative"):
        engine.apply(
            submitted,
            OrderLifecycleEvent("e2", "o1", OrderLifecycleState.PARTIALLY_FILLED, -1, 10.0),
        )
    with pytest.raises(ValueError, match="fill_price"):
        engine.apply(
            submitted,
            OrderLifecycleEvent("e3", "o1", OrderLifecycleState.PARTIALLY_FILLED, 1),
        )
