from __future__ import annotations

from collections import Counter

from rdqp.execution.domain.models import BrokerPosition, ManagedOrder
from rdqp.execution.reconciliation.models import (
    ReconciliationIssue,
    ReconciliationIssueType,
    ReconciliationReport,
    ReconciliationSeverity,
)


class PortfolioReconciler:
    def __init__(
        self, *, quantity_tolerance: float = 1e-9, cost_tolerance: float = 0.01
    ) -> None:
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

        broker_id_counts: Counter[str] = Counter()
        for order in broker_orders:
            broker_order_id = order.broker_order_id
            if broker_order_id is not None:
                broker_id_counts[broker_order_id] += 1

        for duplicate_broker_id, count in sorted(broker_id_counts.items()):
            if count > 1:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.DUPLICATE_BROKER_ORDER_ID,
                        ReconciliationSeverity.ERROR,
                        "",
                        f"Broker order id {duplicate_broker_id} appears {count} times",
                        duplicate_broker_id,
                        None,
                    )
                )

        broker_by_id = {
            order.broker_order_id: order
            for order in broker_orders
            if order.broker_order_id is not None
        }
        local_by_id = {
            order.broker_order_id: order
            for order in local_orders
            if order.broker_order_id is not None
        }

        for order in local_orders:
            broker_id = order.broker_order_id
            if broker_id is None:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.ORPHAN_LOCAL_ORDER,
                        ReconciliationSeverity.WARNING,
                        order.request.symbol.upper(),
                        "Local open order has no broker order id",
                        None,
                        order.order_id,
                    )
                )
                continue
            broker_order = broker_by_id.get(broker_id)
            if broker_order is None:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.ORPHAN_LOCAL_ORDER,
                        ReconciliationSeverity.WARNING,
                        order.request.symbol.upper(),
                        "Local open order is absent from broker",
                        None,
                        broker_id,
                    )
                )
                continue
            if self._order_signature(broker_order) != self._order_signature(order):
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.ORDER_ATTRIBUTE_MISMATCH,
                        ReconciliationSeverity.ERROR,
                        order.request.symbol.upper(),
                        "Matched order attributes differ",
                        str(self._order_signature(broker_order)),
                        str(self._order_signature(order)),
                    )
                )

        for broker_id, order in broker_by_id.items():
            if broker_id not in local_by_id:
                issues.append(
                    ReconciliationIssue(
                        ReconciliationIssueType.ORPHAN_BROKER_ORDER,
                        ReconciliationSeverity.ERROR,
                        order.request.symbol.upper(),
                        "Broker open order is absent locally",
                        broker_id,
                        None,
                    )
                )

        return ReconciliationReport(
            tuple(issues),
            len(broker_positions),
            len(local_positions),
            len(broker_orders),
            len(local_orders),
        )

    @staticmethod
    def _order_signature(order: ManagedOrder) -> tuple[object, ...]:
        request = order.request
        return (
            request.symbol.upper(),
            request.side,
            request.quantity,
            request.order_type,
            request.limit_price,
            request.stop_price,
            order.status,
        )
