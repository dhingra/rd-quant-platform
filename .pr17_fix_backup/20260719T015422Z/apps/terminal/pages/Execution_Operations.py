"""Sprint 14 execution operations dashboard."""

from __future__ import annotations

import os
from dataclasses import asdict

import streamlit as st

from rdqp.execution import (
    AccountSyncService,
    BrokerAccountState,
    IBKRAccountReader,
    PortfolioReconciler,
)
from rdqp.risk.application.live_controls import LiveRiskController, LiveRiskLimits

st.set_page_config(page_title="Execution Operations", layout="wide")
st.title("Execution Operations")
st.warning("PAPER ACCOUNT ONLY — live-account ports and unattended live execution remain disabled.")

st.session_state.setdefault("execution_emergency_paused", True)
st.session_state.setdefault("account_sync_result", None)
st.session_state.setdefault("local_positions", ())
st.session_state.setdefault("local_orders", ())
st.session_state.setdefault("lifecycle_records", ())


def synchronize_account() -> None:
    host = os.getenv("RDQP_IBKR_HOST", "127.0.0.1")
    port = int(os.getenv("RDQP_IBKR_PORT", "7497"))
    client_id = int(os.getenv("RDQP_IBKR_CLIENT_ID", "71"))
    reader = IBKRAccountReader(host, port, client_id)
    try:
        reader.connect(readonly=True)
        st.session_state.account_sync_result = AccountSyncService(reader).synchronize()
    except Exception as exc:  # Streamlit boundary: render provider failures to operator.
        st.session_state.account_sync_error = str(exc)
    finally:
        reader.disconnect()


def state_rows(state: BrokerAccountState | None, attribute: str) -> list[dict[str, object]]:
    if state is None:
        return []
    return [asdict(item) for item in getattr(state, attribute)]


account_tab, reconciliation_tab, lifecycle_tab, risk_tab = st.tabs(
    ["Account Sync", "Reconciliation", "Order Lifecycle", "Live Risk"]
)

with account_tab:
    st.subheader("IBKR account synchronization")
    st.caption(
        "Uses RDQP_IBKR_HOST, RDQP_IBKR_PORT, and RDQP_IBKR_CLIENT_ID. "
        "Only paper ports 7497 and 4002 are accepted."
    )
    if st.button("Synchronize paper account", type="primary"):
        synchronize_account()

    result = st.session_state.account_sync_result
    if error := st.session_state.pop("account_sync_error", None):
        st.error(error)
    if result is None:
        st.info("No account synchronization has been run in this session.")
    else:
        health = result.health
        st.write(f"Connection: **{health.state.value}** — {health.message}")
        st.caption(f"Synchronization latency: {result.duration_ms:.1f} ms")
        state = result.state
        if state is not None:
            snapshot = state.account
            cols = st.columns(4)
            cols[0].metric("Net liquidation", f"{snapshot.net_liquidation:,.2f}")
            cols[1].metric("Cash", f"{snapshot.cash:,.2f}")
            cols[2].metric("Buying power", f"{snapshot.buying_power:,.2f}")
            cols[3].metric("Unrealized P&L", f"{snapshot.unrealized_pnl:,.2f}")
            st.markdown("#### Positions")
            st.dataframe(
                state_rows(state, "account") if False else [asdict(p) for p in snapshot.positions],
                use_container_width=True,
            )
            st.markdown("#### Open orders")
            st.dataframe(state_rows(state, "open_orders"), use_container_width=True)
            st.markdown("#### Executions")
            st.dataframe(state_rows(state, "executions"), use_container_width=True)

with reconciliation_tab:
    st.subheader("Portfolio reconciliation")
    st.caption(
        "Compares broker and local positions and open orders, including orphan and attribute mismatches."
    )
    result = st.session_state.account_sync_result
    state = None if result is None else result.state
    if st.button("Run reconciliation", disabled=state is None):
        assert state is not None
        st.session_state.reconciliation_report = PortfolioReconciler().reconcile(
            state.account.positions,
            tuple(st.session_state.local_positions),
            state.open_orders,
            tuple(st.session_state.local_orders),
        )
    report = st.session_state.get("reconciliation_report")
    if report is None:
        st.info("Synchronize the account, then run reconciliation.")
    else:
        if report.is_reconciled:
            st.success("No error-severity reconciliation issues found.")
        else:
            st.error(f"Reconciliation found {report.error_count} error(s).")
        st.dataframe([asdict(issue) for issue in report.issues], use_container_width=True)

with lifecycle_tab:
    st.subheader("Order lifecycle audit")
    st.caption("NEW → SUBMITTED → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED / CANCELLED / REJECTED")
    records = tuple(st.session_state.lifecycle_records)
    rows = [
        {
            "order_id": record.order_id,
            "state": record.state.value,
            "requested_quantity": record.requested_quantity,
            "filled_quantity": record.filled_quantity,
            "remaining_quantity": record.remaining_quantity,
            "average_fill_price": record.average_fill_price,
            "event_count": len(record.events),
        }
        for record in records
    ]
    st.dataframe(rows, use_container_width=True)
    if not rows:
        st.info("Lifecycle records will appear here when the execution service publishes them.")

with risk_tab:
    st.subheader("Live risk controls")
    paused = st.toggle(
        "Emergency pause",
        value=bool(st.session_state.execution_emergency_paused),
        help="When active, the live-risk controller blocks all new order requests.",
    )
    st.session_state.execution_emergency_paused = paused

    result = st.session_state.account_sync_result
    state = None if result is None else result.state
    if state is None:
        st.warning("Synchronize the paper account before evaluating operational risk.")
    else:
        status = LiveRiskController().evaluate(
            state.account,
            LiveRiskLimits(),
            peak_net_liquidation=state.account.net_liquidation,
            health=result.health,
            market_data_timestamp=state.account.timestamp,
            open_orders=state.open_orders,
            emergency_paused=paused,
        )
        if status.allowed:
            st.success("Operational risk checks passed.")
        else:
            st.error("Order entry is blocked.")
        st.dataframe(
            [{"reason": reason} for reason in status.reasons],
            use_container_width=True,
        )
