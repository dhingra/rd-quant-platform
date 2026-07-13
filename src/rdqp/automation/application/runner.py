"""Risk-gated strategy automation. Live trading is intentionally unsupported."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Protocol

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.automation.domain.models import (
    AutomationConfig,
    AutomationDecision,
    AutomationMode,
    AutomationRun,
)
from rdqp.execution.application.order_manager import OrderManager
from rdqp.execution.domain.models import ExecutionOrderType, ExecutionSide, OrderRequest
from rdqp.risk.domain.models import RiskLimits
from rdqp.strategies.application.evaluator import evaluate_all
from rdqp.strategies.domain.models import StrategyDefinition


class AutomationJournal(Protocol):
    def record(self, run: AutomationRun) -> None: ...


class AutomationRunner:
    def __init__(
        self, order_manager: OrderManager, journal: AutomationJournal | None = None
    ) -> None:
        self._orders = order_manager
        self._journal = journal
        self._last_action: dict[str, datetime] = {}

    def run_cycle(
        self,
        strategy: StrategyDefinition,
        snapshots: list[FactorSnapshot],
        config: AutomationConfig,
        limits: RiskLimits,
        now: datetime | None = None,
    ) -> AutomationRun:
        now = now or datetime.now(timezone.utc)
        if config.mode is AutomationMode.DISABLED:
            run = AutomationRun(
                strategy.name,
                config.mode,
                len(snapshots),
                (AutomationDecision("*", "NONE", "Automation is disabled"),),
                now,
            )
            self._record(run)
            return run

        prices = {s.symbol: s.price for s in snapshots}
        account = self._orders.broker.account_snapshot(prices)
        positions = {p.symbol: p.quantity for p in account.positions if p.quantity != 0}
        decisions: list[AutomationDecision] = []
        submitted_count = 0

        for snap in sorted(snapshots, key=lambda s: (s.rank is None, s.rank or 10**9, s.symbol)):
            in_position = positions.get(snap.symbol, 0) != 0
            action: str | None = None
            reason = ""
            if in_position and config.allow_exits and evaluate_all(snap, strategy.exit_rules):
                action, reason = "SELL", "Exit rules matched"
            elif not in_position and evaluate_all(snap, strategy.entry_rules):
                if config.require_positive_roc and (snap.roc is None or snap.roc <= 0):
                    decisions.append(
                        AutomationDecision(snap.symbol, "SKIP", "Positive ROC guard failed")
                    )
                    continue
                action, reason = "BUY", "Entry rules matched"
            else:
                continue

            previous = self._last_action.get(snap.symbol)
            if previous and (now - previous).total_seconds() < config.cooldown_seconds:
                decisions.append(AutomationDecision(snap.symbol, "SKIP", "Cooldown active"))
                continue
            if action == "BUY" and len(positions) >= config.max_open_positions:
                decisions.append(
                    AutomationDecision(snap.symbol, "SKIP", "Maximum open positions reached")
                )
                continue
            if submitted_count >= config.max_orders_per_cycle:
                decisions.append(
                    AutomationDecision(snap.symbol, "SKIP", "Cycle order limit reached")
                )
                continue
            if config.mode is AutomationMode.DRY_RUN:
                decisions.append(AutomationDecision(snap.symbol, action, f"DRY RUN: {reason}"))
                self._last_action[snap.symbol] = now
                submitted_count += 1
                continue

            request = OrderRequest(
                symbol=snap.symbol,
                side=ExecutionSide.BUY if action == "BUY" else ExecutionSide.SELL,
                quantity=config.quantity
                if action == "BUY"
                else max(1, int(abs(positions.get(snap.symbol, config.quantity)))),
                order_type=ExecutionOrderType.MARKET,
                reference_price=snap.price,
                strategy=strategy.name,
                note="Sprint 7 automation",
            )
            order = self._orders.submit(request, limits, prices)
            was_submitted = order.status.value in {"SUBMITTED", "FILLED", "PARTIALLY_FILLED"}
            decisions.append(
                AutomationDecision(
                    snap.symbol, action, order.message or reason, was_submitted, order.order_id
                )
            )
            if was_submitted:
                self._last_action[snap.symbol] = now
                submitted_count += 1
                if action == "BUY":
                    positions[snap.symbol] = config.quantity
                else:
                    positions.pop(snap.symbol, None)

        if not decisions:
            decisions.append(AutomationDecision("*", "NONE", "No strategy rules matched"))
        run = AutomationRun(strategy.name, config.mode, len(snapshots), tuple(decisions), now)
        self._record(run)
        return run

    def _record(self, run: AutomationRun) -> None:
        if self._journal is not None:
            self._journal.record(run)
