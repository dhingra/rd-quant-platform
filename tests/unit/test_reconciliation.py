from rdqp.execution import BrokerPosition, PortfolioReconciler, ReconciliationIssueType


def test_reconciler_detects_missing_and_mismatch() -> None:
    broker = (BrokerPosition("AAPL", 10, 100, 110), BrokerPosition("MSFT", 5, 200, 210))
    local = (BrokerPosition("AAPL", 9, 99, 110),)
    report = PortfolioReconciler().reconcile(broker, local)
    kinds = {issue.issue_type for issue in report.issues}
    assert ReconciliationIssueType.QUANTITY_MISMATCH in kinds
    assert ReconciliationIssueType.AVERAGE_COST_MISMATCH in kinds
    assert ReconciliationIssueType.MISSING_LOCAL_POSITION in kinds
    assert not report.is_reconciled
