from __future__ import annotations

from rdqp.execution.domain.models import BrokerPosition, ManagedOrder
from rdqp.execution.reconciliation.models import (
    ReconciliationIssue,
    ReconciliationIssueType,
    ReconciliationReport,
    ReconciliationSeverity,
)


class PortfolioReconciler:
    def __init__(self, *, quantity_tolerance: float = 1e-9, cost_tolerance: float = 0.01) -> None:
        self.quantity_tolerance = quantity_tolerance
        self.cost_tolerance = cost_tolerance

    def reconcile(
        self,
        broker_positions: tuple[BrokerPosition, ...],
        local_positions: tuple[BrokerPosition, ...],
        broker_orders: tuple[ManagedOrder, ...] = (),
        local_orders: tuple[ManagedOrder, ...] = (),
    ) -> ReconciliationReport:
        issues: list[ReconciliationIssue] = []
        broker = {p.symbol.upper(): p for p in broker_positions}
        local = {p.symbol.upper(): p for p in local_positions}
        for symbol in sorted(broker.keys() | local.keys()):
            bp, lp = broker.get(symbol), local.get(symbol)
            if bp is None and lp is not None:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.MISSING_BROKER_POSITION,
                        ReconciliationSeverity.ERROR,
                        symbol,
                        "Position exists locally but not at broker",
                        None,
                        lp.quantity,
                    )
                )
                continue
            if lp is None and bp is not None:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.MISSING_LOCAL_POSITION,
                        ReconciliationSeverity.ERROR,
                        symbol,
                        "Position exists at broker but not locally",
                        bp.quantity,
                        None,
                    )
                )
                continue
            assert bp is not None and lp is not None
            if abs(bp.quantity - lp.quantity) > self.quantity_tolerance:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.QUANTITY_MISMATCH,
                        ReconciliationSeverity.ERROR,
                        symbol,
                        "Position quantity differs",
                        bp.quantity,
                        lp.quantity,
                    )
                )
            if abs(bp.average_cost - lp.average_cost) > self.cost_tolerance:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.AVERAGE_COST_MISMATCH,
                        ReconciliationSeverity.WARNING,
                        symbol,
                        "Average cost differs",
                        bp.average_cost,
                        lp.average_cost,
                    )
                )
        broker_ids = {o.broker_order_id for o in broker_orders if o.broker_order_id}
        for order in local_orders:
            if order.broker_order_id and order.broker_order_id not in broker_ids:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.ORPHAN_LOCAL_ORDER,
                        ReconciliationSeverity.WARNING,
                        order.request.symbol.upper(),
                        "Local open order is absent from broker",
                        None,
                        order.broker_order_id,
                    )
                )
        return ReconciliationReport(
            tuple(issues),
            len(broker_positions),
            len(local_positions),
            len(broker_orders),
            len(local_orders),
        )
