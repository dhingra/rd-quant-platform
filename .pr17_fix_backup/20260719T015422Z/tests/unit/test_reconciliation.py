from rdqp.execution import (
    BrokerPosition,
    ExecutionMode,
    ExecutionSide,
    ExecutionStatus,
    ManagedOrder,
    OrderRequest,
    PortfolioReconciler,
    ReconciliationIssueType,
)


def _order(
    order_id: str,
    broker_order_id: str | None,
    *,
    symbol: str = "AAPL",
    quantity: int = 10,
) -> ManagedOrder:
    return ManagedOrder(
        order_id,
        OrderRequest(symbol, ExecutionSide.BUY, quantity),
        ExecutionMode.PAPER,
        ExecutionStatus.SUBMITTED,
        broker_order_id=broker_order_id,
    )


def test_reconciler_detects_missing_and_mismatch() -> None:
    broker = (
        BrokerPosition("AAPL", 10, 100, 110),
        BrokerPosition("MSFT", 5, 200, 210),
    )
    local = (BrokerPosition("AAPL", 9, 99, 110),)
    report = PortfolioReconciler().reconcile(broker, local)
    kinds = {issue.issue_type for issue in report.issues}
    assert ReconciliationIssueType.QUANTITY_MISMATCH in kinds
    assert ReconciliationIssueType.AVERAGE_COST_MISMATCH in kinds
    assert ReconciliationIssueType.MISSING_LOCAL_POSITION in kinds
    assert not report.is_reconciled


def test_reconciler_detects_orders_on_both_sides_and_attributes() -> None:
    broker_orders = (_order("b1", "101"), _order("b2", "102", symbol="MSFT"))
    local_orders = (
        _order("l1", "101", quantity=9),
        _order("l2", None),
        _order("l3", "999"),
    )
    report = PortfolioReconciler().reconcile(
        (), (), broker_orders=broker_orders, local_orders=local_orders
    )
    kinds = {issue.issue_type for issue in report.issues}
    assert ReconciliationIssueType.ORDER_ATTRIBUTE_MISMATCH in kinds
    assert ReconciliationIssueType.ORPHAN_LOCAL_ORDER in kinds
    assert ReconciliationIssueType.ORPHAN_BROKER_ORDER in kinds
