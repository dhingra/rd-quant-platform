"""Sprint 12 portfolio intelligence workstation page."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from rdqp.portfolio_intelligence import (
    OptimizationObjective,
    PortfolioConstraints,
    PortfolioOptimizer,
    StressScenario,
    analyze_risk,
    build_rebalance_plan,
    run_stress_tests,
)

st.set_page_config(page_title="Portfolio Intelligence", page_icon="🧮", layout="wide")
st.title("Portfolio Intelligence")
st.caption("Upload aligned periodic returns with one column per symbol.")

uploaded = st.file_uploader("Returns CSV", type=["csv"])
if uploaded is None:
    st.info("CSV example: date,AAPL,MSFT,JPM with decimal returns such as 0.01.")
    st.stop()

frame = pd.read_csv(uploaded)
numeric = frame.select_dtypes(include="number").dropna()
if numeric.shape[1] < 2 or len(numeric) < 2:
    st.error("Provide at least two numeric symbol columns and two observations.")
    st.stop()

returns = {column: numeric[column].astype(float).tolist() for column in numeric.columns}
objective = OptimizationObjective(
    st.selectbox("Objective", [item.value for item in OptimizationObjective])
)
max_weight = st.slider("Maximum symbol weight", 0.05, 1.0, 0.50, 0.05)
risk_free = st.number_input("Annual risk-free rate", value=0.0, step=0.005)
constraints = PortfolioConstraints(max_weight=max_weight)

try:
    solution = PortfolioOptimizer().optimize(returns, objective, constraints, risk_free)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

weights = {item.symbol: item.weight for item in solution.weights}
report = analyze_risk(returns, weights)

c1, c2, c3 = st.columns(3)
c1.metric("Expected return", f"{solution.expected_return:.2%}")
c2.metric("Volatility", f"{solution.volatility:.2%}")
c3.metric("Sharpe", f"{solution.sharpe_ratio:.2f}")

weight_frame = pd.DataFrame(
    [{"symbol": item.symbol, "weight": item.weight} for item in solution.weights]
)
st.plotly_chart(px.pie(weight_frame, names="symbol", values="weight", title="Target allocation"))

risk_frame = pd.DataFrame(
    [
        {
            "symbol": item.symbol,
            "risk_contribution": item.percentage,
            "component_volatility": item.component,
        }
        for item in report.contributions
    ]
)
st.plotly_chart(
    px.bar(risk_frame, x="symbol", y="risk_contribution", title="Percentage risk contribution")
)

st.subheader("Tail risk")
st.dataframe(
    pd.DataFrame(
        [
            {
                "VaR 95%": report.value_at_risk_95,
                "VaR 99%": report.value_at_risk_99,
                "Expected Shortfall 95%": report.expected_shortfall_95,
                "Maximum Drawdown": report.maximum_drawdown,
            }
        ]
    )
)

st.subheader("Stress test")
shock = st.slider("Uniform market shock", -0.50, 0.20, -0.10, 0.01)
stress = run_stress_tests(
    weights,
    100_000.0,
    [StressScenario("Custom market shock", {symbol: shock for symbol in weights})],
)[0]
st.metric("Stress P&L on $100,000", f"${stress.pnl_value:,.0f}")

current_text = st.text_area(
    "Current weights JSON",
    value=json.dumps({symbol: 1 / len(weights) for symbol in weights}, indent=2),
)
try:
    current = {str(key): float(value) for key, value in json.loads(current_text).items()}
    plan = build_rebalance_plan(current, weights, 100_000.0, cost_bps=5)
    st.subheader("Rebalance plan")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "symbol": trade.symbol,
                    "current_weight": trade.current_weight,
                    "target_weight": trade.target_weight,
                    "weight_change": trade.weight_change,
                    "notional": trade.notional,
                    "estimated_cost": trade.estimated_cost,
                }
                for trade in plan.trades
            ]
        )
    )
except (ValueError, TypeError, json.JSONDecodeError) as exc:
    st.warning(f"Current-weight input is invalid: {exc}")
