"""Sprint 14 execution operations dashboard."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Execution Operations", layout="wide")
st.title("Execution Operations")
st.warning("PAPER ACCOUNT ONLY — live-account ports and unattended live execution remain disabled.")

account, reconciliation, lifecycle, risk = st.tabs(
    ["Account Sync", "Reconciliation", "Order Lifecycle", "Live Risk"]
)
with account:
    st.subheader("IBKR account synchronization")
    st.info(
        "Connect through the configured read-only IBKR paper adapter to display balances, positions, open orders, executions, health, and synchronization latency."
    )
    cols = st.columns(4)
    for col, label in zip(
        cols, ["Net liquidation", "Cash", "Buying power", "Unrealized P&L"], strict=True
    ):
        col.metric(label, "—")
with reconciliation:
    st.subheader("Portfolio reconciliation")
    st.caption("Compares broker and local positions, average cost, quantities, and open orders.")
    st.button("Run reconciliation", type="primary")
    st.dataframe([], use_container_width=True)
with lifecycle:
    st.subheader("Order lifecycle audit")
    st.caption("NEW → SUBMITTED → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED / CANCELLED / REJECTED")
    st.dataframe([], use_container_width=True)
with risk:
    st.subheader("Live risk controls")
    st.toggle(
        "Emergency pause",
        value=True,
        help="Keep enabled until a paper session is explicitly armed.",
    )
    st.success("Paper-mode safety boundary active")
    st.dataframe([], use_container_width=True)
