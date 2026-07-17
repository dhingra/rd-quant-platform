"""Sprint 13 Factor & Regime Lab workstation page."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from rdqp.factor_lab import (
    FactorDefinition,
    FactorNormalizer,
    FactorObservation,
    NormalizationMethod,
    RegimeEngine,
    RegimeObservation,
    RiskRegime,
    StrategyRegimePerformance,
    StrategySelectionConfig,
    StrategySelectionEngine,
)
from rdqp.strategies.infrastructure import YamlStrategyRepository


ROOT = Path(__file__).resolve().parents[3]

st.set_page_config(page_title="Factor & Regime Lab", page_icon="🧭", layout="wide")
st.title("Factor & Regime Lab")
st.caption(
    "Normalize cross-sectional factors, classify the market regime, and rank saved "
    "strategies for the current environment. Recommendations are research outputs, "
    "not automatic order instructions."
)

factor_tab, regime_tab, selection_tab = st.tabs(
    ["Factor leaderboard", "Market regime", "Strategy selection"]
)

with factor_tab:
    st.subheader("Cross-sectional factor leaderboard")
    uploaded = st.file_uploader(
        "Upload CSV with symbol and one or more numeric factor columns",
        type=["csv"],
        key="factor_lab_upload",
    )
    if uploaded is None:
        frame = pd.DataFrame(
            {
                "symbol": ["AAPL", "MSFT", "NVDA", "AMZN", "META"],
                "momentum": [0.012, 0.006, 0.028, -0.004, 0.017],
                "rvol": [1.2, 0.9, 2.4, 1.1, 1.7],
            }
        )
        st.caption("Using example data. Upload a CSV to replace it.")
    else:
        frame = pd.read_csv(uploaded)

    if "symbol" not in frame.columns:
        st.error("CSV must contain a symbol column.")
    else:
        numeric = [
            column
            for column in frame.columns
            if column != "symbol" and pd.api.types.is_numeric_dtype(frame[column])
        ]
        if not numeric:
            st.warning("Add at least one numeric factor column.")
        else:
            c1, c2, c3 = st.columns(3)
            factor_name = c1.selectbox("Factor", numeric)
            method = NormalizationMethod(
                c2.selectbox("Normalization", [item.value for item in NormalizationMethod])
            )
            higher_is_better = c3.toggle("Higher is better", value=True)
            timestamp = datetime.now(UTC)
            observations = tuple(
                FactorObservation(
                    str(row["symbol"]),
                    timestamp,
                    {factor_name: float(row[factor_name])},
                )
                for _, row in frame.dropna(subset=[factor_name]).iterrows()
            )
            section = FactorNormalizer().normalize(
                FactorDefinition(factor_name, higher_is_better=higher_is_better),
                observations,
                method,
            )
            scores = pd.DataFrame(
                [
                    {
                        "symbol": item.symbol,
                        "raw_value": item.raw_value,
                        "winsorized_value": item.winsorized_value,
                        "score": item.score,
                        "percentile": item.percentile,
                    }
                    for item in sorted(section.scores, key=lambda value: value.score, reverse=True)
                ]
            )
            st.dataframe(scores, use_container_width=True, hide_index=True)
            st.plotly_chart(
                px.bar(
                    scores,
                    x="symbol",
                    y="score",
                    title=f"{factor_name} normalized score",
                ),
                use_container_width=True,
            )

with regime_tab:
    st.subheader("Deterministic market-regime classifier")
    r1, r2, r3 = st.columns(3)
    trend_return = r1.number_input("Trend return", value=0.015, format="%.4f")
    annualized_volatility = r2.number_input(
        "Annualized volatility", min_value=0.0, value=0.18, format="%.4f"
    )
    positive_breadth = r3.slider("Positive breadth", 0.0, 1.0, 0.62, 0.01)
    current_regime = RegimeEngine().classify(
        RegimeObservation(
            datetime.now(UTC),
            float(trend_return),
            float(annualized_volatility),
            float(positive_breadth),
        )
    )
    st.session_state.factor_lab_regime = current_regime
    metrics = st.columns(5)
    metrics[0].metric("Trend", current_regime.trend.value)
    metrics[1].metric("Volatility", current_regime.volatility.value)
    metrics[2].metric("Breadth", current_regime.breadth.value)
    metrics[3].metric("Composite", current_regime.risk.value)
    metrics[4].metric("Confidence", f"{current_regime.confidence:.0%}")

with selection_tab:
    st.subheader("Regime-aware strategy selection")
    regime = st.session_state.get("factor_lab_regime")
    if regime is None:
        regime = RegimeEngine().classify(
            RegimeObservation(datetime.now(UTC), 0.0, 0.20, 0.50)
        )

    repository = YamlStrategyRepository(ROOT / "data/saved_strategies.yaml")
    strategies = repository.list()
    names = [item.name for item in strategies] or ["Momentum", "Breakout", "Mean Reversion"]
    default_rows = pd.DataFrame(
        [
            {
                "strategy": name,
                "regime": regime.risk.value,
                "total_return": 0.08 - index * 0.015,
                "sharpe": 1.4 - index * 0.15,
                "max_drawdown": -0.10 - index * 0.02,
                "profit_factor": 1.7 - index * 0.1,
                "trade_count": 20,
            }
            for index, name in enumerate(names)
        ]
    )
    edited = st.data_editor(
        default_rows,
        use_container_width=True,
        hide_index=True,
        disabled=["strategy", "regime"],
        key="strategy_regime_performance",
    )
    s1, s2, s3 = st.columns(3)
    minimum_trades = int(s1.number_input("Minimum trades", 0, 500, 5))
    maximum_drawdown = float(s2.slider("Maximum drawdown", -1.0, 0.0, -0.30, 0.01))
    maximum_strategies = int(s3.number_input("Maximum ensemble strategies", 1, 10, 3))

    records = tuple(
        StrategyRegimePerformance(
            str(row.strategy),
            RiskRegime(str(row.regime)),
            float(row.total_return),
            float(row.sharpe),
            float(row.max_drawdown),
            float(row.profit_factor),
            int(row.trade_count),
        )
        for row in edited.itertuples(index=False)
    )
    result = StrategySelectionEngine(
        StrategySelectionConfig(
            minimum_trades=minimum_trades,
            maximum_drawdown=maximum_drawdown,
            maximum_strategies=maximum_strategies,
        )
    ).select(regime, records)

    recommendations = pd.DataFrame(
        [
            {
                "strategy": item.strategy_name,
                "score": item.score,
                "eligible": item.eligible,
                "reasons": "; ".join(item.reasons),
            }
            for item in result.recommendations
        ]
    )
    st.markdown(f"#### Recommendations for `{regime.risk.value}`")
    st.dataframe(recommendations, use_container_width=True, hide_index=True)

    allocations = pd.DataFrame(
        [
            {
                "strategy": item.strategy_name,
                "weight": item.weight,
                "score": item.score,
            }
            for item in result.allocations
        ]
    )
    if allocations.empty:
        st.warning("No strategy passed the current eligibility gates.")
    else:
        left, right = st.columns(2)
        left.dataframe(allocations, use_container_width=True, hide_index=True)
        right.plotly_chart(
            px.pie(allocations, names="strategy", values="weight", title="Suggested ensemble"),
            use_container_width=True,
        )
        st.info("Paper deployment remains operator-controlled; no orders are submitted from this page.")
