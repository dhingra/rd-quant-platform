"""RD Quant Terminal — Sprint 10 cumulative quant intelligence platform."""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rdqp.dashboard.application.controller import DashboardController
from rdqp.market.domain.models import Tick
from rdqp.datasources.ibkr.snapshot import fetch_snapshot_ticks
from rdqp.datasources.yahoo.snapshot import fetch_latest_ticks
from rdqp.platform.config.settings import load_settings
from rdqp.scanners import FilterOperator, ScanDefinition, ScannerFilter, default_scans
from rdqp.scanners.infrastructure.yaml_repository import YamlScanRepository
from rdqp.portfolio import PaperPortfolio
from rdqp.execution import (
    ExecutionOrderType,
    ExecutionSide,
    IBKRPaperBroker,
    OrderManager,
    OrderRequest,
    PaperExecutionBroker,
    SQLiteTradeJournal,
)
from rdqp.risk import RiskLimits
from rdqp.strategies import BacktestEngine, RuleOperator, StrategyDefinition, StrategyRule
from rdqp.strategies.infrastructure import YamlStrategyRepository
from rdqp.research.application.comparison import compare_strategies
from rdqp.research.application.metrics import extended_metrics
from rdqp.research.application.robustness import analyze_robustness
from rdqp.research.application.scorecard import ScorecardEngine
from rdqp.research.application.monte_carlo import MonteCarloEngine
from rdqp.research.application.optimizer import GridSearchOptimizer
from rdqp.research.application.walk_forward import WalkForwardEngine
from rdqp.research.domain.models import (
    OptimizationObjective,
    ParameterRange,
    ResearchExperiment,
)
from rdqp.research.infrastructure.sqlite_repository import SqliteExperimentRepository
from rdqp.replay import CsvTickStore, ReplayEngine
from rdqp.observability import HealthMonitor, HealthStatus, MetricsRegistry
from rdqp.automation import (
    AutomationConfig,
    AutomationMode,
    AutomationRunner,
    JsonlAutomationJournal,
    AutomationScheduler,
    MarketSessionPolicy,
    SchedulerConfig,
    SQLiteAutomationStateStore,
)
from rdqp.notifications import (
    InMemoryNotificationSink,
    JsonlNotificationSink,
    NotificationRouter,
)

st.set_page_config(page_title="RD Quant Platform", page_icon="📈", layout="wide")
settings = load_settings(ROOT / "config/app.yaml")


def parse_symbols(raw: str) -> list[str]:
    return list(
        dict.fromkeys(
            part.strip().upper() for part in raw.replace("\n", ",").split(",") if part.strip()
        )
    )


def as_frame(records) -> pd.DataFrame:
    rows = [
        {
            "rank": r.rank,
            "symbol": r.symbol,
            "sector": r.sector,
            "price": r.price,
            "roc_pct": None if r.roc is None else r.roc * 100,
            "rvol": r.rvol,
            "vwap": r.vwap,
            "vwap_distance_pct": None if r.vwap_distance is None else r.vwap_distance * 100,
            "gap_pct": None if r.gap is None else r.gap * 100,
            "volume": r.volume,
            "orb": r.opening_range_state,
            "datetime": r.timestamp,
        }
        for r in records
    ]
    return pd.DataFrame(rows)


def controller_key(source: str, symbols: list[str], window: int) -> tuple[object, ...]:
    return source, tuple(symbols), window


with st.sidebar:
    st.header("Control Panel")
    source = st.radio("Data source", ["Simulator", "Yahoo Finance", "IBKR Paper / Gateway"])
    raw_symbols = st.text_area("Watchlist", ", ".join(settings.market_data.watchlist), height=125)
    symbols = parse_symbols(raw_symbols)
    lookback = st.slider("ROC lookback seconds", 60, 900, settings.analytics.roc_window_seconds, 30)
    leaderboard_size = st.slider("Leaderboard size", 5, 50, 10)
    simulator_steps = st.slider("Simulator steps per refresh", 1, 30, 5)
    st.caption(
        "Yahoo supplies delayed 1-minute bars. IBKR uses a read-only paper snapshot connection."
    )

key = controller_key(source, symbols, lookback)
if st.session_state.get("dashboard_key") != key:
    st.session_state.dashboard_key = key
    st.session_state.controller = DashboardController(symbols, lookback)
    st.session_state.selected_symbol = symbols[0] if symbols else None
    if source == "Simulator":
        st.session_state.controller.simulator_refresh(lookback + 35)

controller: DashboardController = st.session_state.controller


def refresh() -> None:
    if source == "Simulator":
        controller.simulator_refresh(simulator_steps)
    elif source == "Yahoo Finance":
        ticks = fetch_latest_ticks(
            symbols, settings.market_data.yahoo.period, settings.market_data.yahoo.interval
        )
        controller.ingest(ticks)
    else:
        ib = settings.market_data.ibkr
        ticks = fetch_snapshot_ticks(symbols, ib.host, ib.port, ib.client_id, ib.market_data_type)
        controller.ingest(ticks)


header_left, header_right = st.columns([5, 1])
with header_left:
    st.title("RD Quant Platform")
    st.caption("Sprint 10 · Quant Intelligence · scorecards · robustness · factor ranking")
with header_right:
    if st.button("Refresh data", type="primary", use_container_width=True):
        try:
            with st.spinner(f"Refreshing {source}..."):
                refresh()
        except Exception as exc:
            st.error(str(exc))

if not controller.records() and source != "Simulator":
    st.info("Press **Refresh data** to load market data.")

records = controller.records()
df = as_frame(records)
stats = controller.statistics()

metric_cols = st.columns(6)
metric_cols[0].metric("Symbols ranked", stats.count)
metric_cols[1].metric(
    "Mean ROC", "n/a" if stats.mean_roc is None else f"{stats.mean_roc * 100:+.3f}%"
)
metric_cols[2].metric(
    "Median ROC", "n/a" if stats.median_roc is None else f"{stats.median_roc * 100:+.3f}%"
)
metric_cols[3].metric(
    "Std dev",
    "n/a" if stats.standard_deviation is None else f"{stats.standard_deviation * 100:.3f}%",
)
metric_cols[4].metric("Skew", "n/a" if stats.skew is None else f"{stats.skew:+.2f}")
metric_cols[5].metric(
    "Positive", "n/a" if stats.positive_percentage is None else f"{stats.positive_percentage:.0%}"
)

page = st.segmented_control(
    "View",
    [
        "Leaderboard",
        "Scanner",
        "Strategy Lab",
        "Research Lab",
        "Execution",
        "Automation",
        "Scheduler & Alerts",
        "Market",
        "Replay & Ops",
        "Architecture",
    ],
    default="Leaderboard",
)

if page == "Leaderboard":
    st.subheader("Live cross-sectional momentum")
    left, right = st.columns(2)
    display_cols = [
        "rank",
        "symbol",
        "sector",
        "price",
        "roc_pct",
        "rvol",
        "vwap_distance_pct",
        "orb",
    ]
    with left:
        st.markdown("#### Leaders")
        leaders = df.head(leaderboard_size)[display_cols] if not df.empty else df
        leader_event = st.dataframe(
            leaders,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="leaders_table",
            column_config={
                "price": st.column_config.NumberColumn(format="$%.2f"),
                "roc_pct": st.column_config.NumberColumn("ROC %", format="%+.3f%%"),
                "rvol": st.column_config.NumberColumn(format="%.2f"),
                "vwap_distance_pct": st.column_config.NumberColumn("VWAP dist %", format="%+.3f%%"),
            },
        )
        if leader_event.selection.rows:
            st.session_state.selected_symbol = leaders.iloc[leader_event.selection.rows[0]][
                "symbol"
            ]
    with right:
        st.markdown("#### Laggards")
        laggards = (
            df.tail(leaderboard_size).sort_values("roc_pct")[display_cols] if not df.empty else df
        )
        laggard_event = st.dataframe(
            laggards,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="laggards_table",
            column_config={
                "price": st.column_config.NumberColumn(format="$%.2f"),
                "roc_pct": st.column_config.NumberColumn("ROC %", format="%+.3f%%"),
                "rvol": st.column_config.NumberColumn(format="%.2f"),
                "vwap_distance_pct": st.column_config.NumberColumn("VWAP dist %", format="%+.3f%%"),
            },
        )
        if laggard_event.selection.rows:
            st.session_state.selected_symbol = laggards.iloc[laggard_event.selection.rows[0]][
                "symbol"
            ]

    chart_left, chart_right = st.columns(2)
    valid = df.dropna(subset=["roc_pct"]) if not df.empty else df
    with chart_left:
        st.markdown("#### ROC distribution")
        if valid.empty:
            st.info("ROC needs enough event-time history for the selected lookback.")
        else:
            fig = px.histogram(
                valid, x="roc_pct", nbins=min(20, max(5, len(valid))), hover_data=["symbol"]
            )
            fig.add_vline(x=0, line_dash="dash")
            fig.update_layout(xaxis_title="ROC %", yaxis_title="Symbols", height=340)
            st.plotly_chart(fig, use_container_width=True)
    with chart_right:
        st.markdown("#### Momentum breadth")
        positive = stats.positive_percentage * 100 if stats.positive_percentage is not None else 0
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=positive,
                number={"suffix": "%"},
                title={"text": "Symbols with positive ROC"},
                gauge={"axis": {"range": [0, 100]}},
            )
        )
        gauge.update_layout(height=340, margin=dict(l=30, r=30, t=70, b=20))
        st.plotly_chart(gauge, use_container_width=True)

    st.divider()
    selected = st.session_state.get("selected_symbol")
    if selected and not df.empty and selected in set(df.symbol):
        st.subheader(f"Selected symbol · {selected}")
        selected_row = df[df.symbol == selected].iloc[0]
        cards = st.columns(6)
        cards[0].metric("Last", f"${selected_row.price:,.2f}")
        cards[1].metric(
            "ROC", "n/a" if pd.isna(selected_row.roc_pct) else f"{selected_row.roc_pct:+.3f}%"
        )
        cards[2].metric("Rank", int(selected_row["rank"]))
        cards[3].metric("RVOL", "n/a" if pd.isna(selected_row.rvol) else f"{selected_row.rvol:.2f}")
        cards[4].metric(
            "VWAP distance",
            "n/a"
            if pd.isna(selected_row.vwap_distance_pct)
            else f"{selected_row.vwap_distance_pct:+.3f}%",
        )
        cards[5].metric("ORB", selected_row.orb)

        history = controller.symbol_history(selected)
        history_df = pd.DataFrame(
            {
                "datetime": [r.timestamp for r in history],
                "price": [r.price for r in history],
                "roc_pct": [None if r.roc is None else r.roc * 100 for r in history],
                "vwap": [r.vwap for r in history],
                "volume": [r.volume for r in history],
            }
        )
        price_col, roc_col = st.columns(2)
        with price_col:
            price_chart = go.Figure()
            price_chart.add_trace(
                go.Scatter(x=history_df.datetime, y=history_df.price, name="Price")
            )
            price_chart.add_trace(go.Scatter(x=history_df.datetime, y=history_df.vwap, name="VWAP"))
            price_chart.update_layout(title="Price and VWAP", height=350, yaxis_title="Price")
            st.plotly_chart(price_chart, use_container_width=True)
        with roc_col:
            roc_chart = px.line(history_df, x="datetime", y="roc_pct", title="Event-time ROC")
            roc_chart.add_hline(y=0, line_dash="dash")
            roc_chart.update_layout(height=350, yaxis_title="ROC %")
            st.plotly_chart(roc_chart, use_container_width=True)
        volume_chart = px.bar(history_df.tail(120), x="datetime", y="volume", title="Recent volume")
        volume_chart.update_layout(height=280)
        st.plotly_chart(volume_chart, use_container_width=True)

elif page == "Scanner":
    st.subheader("Configurable scanner engine")
    st.caption(
        "Composable filters run against the latest cross-sectional factor snapshot. Saved scans persist to data/saved_scans.yaml."
    )

    if "scan_repository" not in st.session_state:
        st.session_state.scan_repository = YamlScanRepository(ROOT / "data/saved_scans.yaml")
    if "scanner_alert_log" not in st.session_state:
        st.session_state.scanner_alert_log = []
    repository = st.session_state.scan_repository

    builtins = {scan.name: scan for scan in default_scans()}
    saved = {scan.name: scan for scan in repository.list()}
    scans = {**builtins, **saved}

    preset_col, alert_col = st.columns([3, 1])
    with preset_col:
        selected_scan_name = st.selectbox("Scanner", list(scans), key="selected_scan_name")
    with alert_col:
        alerts_enabled = st.toggle("New-match alerts", value=True)

    definition = scans[selected_scan_name]
    with st.expander("Scanner definition", expanded=False):
        st.write(definition.description or "No description")
        st.json(
            {
                "sort_by": definition.sort_by,
                "descending": definition.descending,
                "limit": definition.limit,
                "filters": [
                    {
                        "field": f.field,
                        "operator": f.operator.value,
                        "value": f.value,
                        "second_value": f.second_value,
                    }
                    for f in definition.filters
                ],
            }
        )

    result = controller.run_scan(definition)
    if alerts_enabled:
        new_alerts = controller.evaluate_alerts(result)
        st.session_state.scanner_alert_log = (
            list(new_alerts) + st.session_state.scanner_alert_log[:99]
        )

    summary_cols = st.columns(4)
    summary_cols[0].metric("Matches", len(result.matches))
    summary_cols[1].metric("Universe", result.evaluated_count)
    summary_cols[2].metric(
        "Match rate", f"{len(result.matches) / max(1, result.evaluated_count):.1%}"
    )
    summary_cols[3].metric("Scan latency", f"{result.elapsed_ms:.3f} ms")

    match_df = pd.DataFrame([match.values for match in result.matches])
    if match_df.empty:
        st.info("No symbols currently satisfy this scan.")
    else:
        visible = [
            c
            for c in [
                "rank",
                "symbol",
                "sector",
                "price",
                "roc_pct",
                "rvol",
                "gap_pct",
                "vwap_distance_pct",
                "opening_range_state",
                "volume",
            ]
            if c in match_df.columns
        ]
        scan_event = st.dataframe(
            match_df[visible],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="scanner_results",
            column_config={
                "price": st.column_config.NumberColumn(format="$%.2f"),
                "roc_pct": st.column_config.NumberColumn("ROC %", format="%+.3f%%"),
                "gap_pct": st.column_config.NumberColumn("Gap %", format="%+.2f%%"),
                "vwap_distance_pct": st.column_config.NumberColumn(
                    "VWAP distance %", format="%+.3f%%"
                ),
                "rvol": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        if scan_event.selection.rows:
            selected_index = scan_event.selection.rows[0]
            st.session_state.selected_symbol = str(match_df.iloc[selected_index]["symbol"])
            st.success(
                f"Selected {st.session_state.selected_symbol}. Open Leaderboard to inspect its charts."
            )

    st.divider()
    builder, alert_panel = st.columns([3, 2])
    with builder:
        st.markdown("#### Build and save a custom scan")
        with st.form("custom_scan_form"):
            custom_name = st.text_input("Name", value="My Momentum Scan")
            custom_description = st.text_input("Description", value="Custom cross-sectional filter")
            field_options = [
                "roc_pct",
                "rvol",
                "gap_pct",
                "vwap_distance_pct",
                "price",
                "volume",
                "rank",
                "sector",
                "above_vwap",
                "orb_breakout",
                "orb_breakdown",
            ]
            c1, c2, c3 = st.columns(3)
            custom_field = c1.selectbox("Field", field_options)
            boolean_field = custom_field in {"above_vwap", "orb_breakout", "orb_breakdown"}
            operators = (
                [FilterOperator.IS_TRUE.value, FilterOperator.IS_FALSE.value]
                if boolean_field
                else [
                    op.value
                    for op in [
                        FilterOperator.GTE,
                        FilterOperator.GT,
                        FilterOperator.LTE,
                        FilterOperator.LT,
                        FilterOperator.EQ,
                        FilterOperator.NE,
                    ]
                ]
            )
            custom_operator = c2.selectbox("Operator", operators)
            if custom_field == "sector":
                custom_value = c3.text_input("Value", value="Technology")
            elif boolean_field:
                custom_value = None
                c3.write("Boolean filter")
            else:
                custom_value = c3.number_input("Value", value=0.0, step=0.1, format="%.4f")
            sort_options = [
                "roc_pct",
                "rvol",
                "gap_pct",
                "vwap_distance_pct",
                "price",
                "volume",
                "rank",
            ]
            s1, s2, s3 = st.columns(3)
            sort_by = s1.selectbox("Sort by", sort_options)
            descending = s2.toggle("Descending", value=True)
            scan_limit = s3.number_input("Limit", min_value=1, max_value=500, value=50)
            save_scan = st.form_submit_button("Save scan", type="primary")
        if save_scan:
            new_definition = ScanDefinition(
                name=custom_name.strip(),
                description=custom_description.strip(),
                filters=(
                    ScannerFilter(custom_field, FilterOperator(custom_operator), custom_value),
                ),
                sort_by=sort_by,
                descending=descending,
                limit=int(scan_limit),
            )
            repository.save(new_definition)
            st.success(f"Saved scan: {new_definition.name}")
            st.rerun()

        if saved:
            delete_name = st.selectbox(
                "Delete saved scan", ["—"] + sorted(saved), key="delete_scan_name"
            )
            if st.button("Delete selected scan", disabled=delete_name == "—"):
                repository.delete(delete_name)
                st.success(f"Deleted scan: {delete_name}")
                st.rerun()

    with alert_panel:
        st.markdown("#### Alert feed")
        alerts = st.session_state.scanner_alert_log
        if not alerts:
            st.caption("No new scanner entries yet.")
        else:
            for alert in alerts[:20]:
                st.markdown(f"**{alert.symbol}** · {alert.scan_name}")
                st.caption(alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S UTC"))

elif page == "Strategy Lab":
    st.subheader("Strategy Lab")
    st.caption(
        "Build factor rules, backtest them against the current event-time history, and place simulated orders in an isolated paper portfolio."
    )

    if "strategy_repository" not in st.session_state:
        st.session_state.strategy_repository = YamlStrategyRepository(
            ROOT / "data/saved_strategies.yaml"
        )
    if "paper_portfolio" not in st.session_state:
        st.session_state.paper_portfolio = PaperPortfolio(100_000.0)
    repository = st.session_state.strategy_repository
    portfolio: PaperPortfolio = st.session_state.paper_portfolio

    field_options = [
        "roc_pct",
        "rvol",
        "vwap_distance_pct",
        "gap_pct",
        "price",
        "volume",
        "rank",
        "above_vwap",
        "orb_breakout",
        "orb_breakdown",
    ]
    numeric_operators = [
        RuleOperator.GT.value,
        RuleOperator.GTE.value,
        RuleOperator.LT.value,
        RuleOperator.LTE.value,
        RuleOperator.EQ.value,
        RuleOperator.NE.value,
    ]

    builder_tab, results_tab, paper_tab = st.tabs(
        ["Visual builder", "Backtest results", "Paper portfolio"]
    )
    with builder_tab:
        saved_strategies = {item.name: item for item in repository.list()}
        if saved_strategies:
            loaded_name = st.selectbox("Load saved strategy", ["—"] + sorted(saved_strategies))
        else:
            loaded_name = "—"
        loaded = saved_strategies.get(loaded_name)

        with st.form("strategy_builder"):
            strategy_name = st.text_input(
                "Strategy name", value=loaded.name if loaded else "Momentum + VWAP"
            )
            description = st.text_input(
                "Description",
                value=loaded.description
                if loaded
                else "Long when momentum and price location agree",
            )
            st.markdown("#### Entry rules (all must pass)")
            entry_rules = []
            default_entries = (
                loaded.entry_rules
                if loaded
                else (
                    StrategyRule("roc_pct", RuleOperator.GT, 0.10),
                    StrategyRule("above_vwap", RuleOperator.IS_TRUE, True),
                )
            )
            entry_count = st.number_input(
                "Number of entry rules", 1, 3, min(3, max(1, len(default_entries)))
            )
            for i in range(int(entry_count)):
                default_rule = (
                    default_entries[i]
                    if i < len(default_entries)
                    else StrategyRule("rvol", RuleOperator.GT, 1.0)
                )
                c1, c2, c3 = st.columns(3)
                field = c1.selectbox(
                    "Field",
                    field_options,
                    index=field_options.index(default_rule.field),
                    key=f"entry_field_{i}",
                )
                is_bool = field in {"above_vwap", "orb_breakout", "orb_breakdown"}
                allowed_ops = (
                    [RuleOperator.IS_TRUE.value, RuleOperator.IS_FALSE.value]
                    if is_bool
                    else numeric_operators
                )
                default_op = (
                    default_rule.operator.value
                    if default_rule.operator.value in allowed_ops
                    else allowed_ops[0]
                )
                operator = c2.selectbox(
                    "Operator",
                    allowed_ops,
                    index=allowed_ops.index(default_op),
                    key=f"entry_op_{i}",
                )
                if is_bool:
                    c3.caption("Boolean condition")
                    value = True
                else:
                    numeric_default = (
                        float(default_rule.value)
                        if isinstance(default_rule.value, (int, float))
                        else 0.0
                    )
                    value = c3.number_input(
                        "Value",
                        value=numeric_default,
                        step=0.1,
                        format="%.4f",
                        key=f"entry_value_{i}",
                    )
                entry_rules.append(StrategyRule(field, RuleOperator(operator), value))

            st.markdown("#### Exit rule")
            use_exit = st.toggle("Use factor exit rule", value=bool(loaded and loaded.exit_rules))
            exit_rules = []
            if use_exit:
                default_exit = (
                    loaded.exit_rules[0]
                    if loaded and loaded.exit_rules
                    else StrategyRule("roc_pct", RuleOperator.LT, 0.0)
                )
                e1, e2, e3 = st.columns(3)
                exit_field = e1.selectbox(
                    "Exit field", field_options, index=field_options.index(default_exit.field)
                )
                exit_bool = exit_field in {"above_vwap", "orb_breakout", "orb_breakdown"}
                exit_ops = (
                    [RuleOperator.IS_TRUE.value, RuleOperator.IS_FALSE.value]
                    if exit_bool
                    else numeric_operators
                )
                exit_operator = e2.selectbox(
                    "Exit operator",
                    exit_ops,
                    index=exit_ops.index(default_exit.operator.value)
                    if default_exit.operator.value in exit_ops
                    else 0,
                )
                if exit_bool:
                    e3.caption("Boolean condition")
                    exit_value = True
                else:
                    exit_value = e3.number_input(
                        "Exit value", value=float(default_exit.value or 0), step=0.1, format="%.4f"
                    )
                exit_rules.append(StrategyRule(exit_field, RuleOperator(exit_operator), exit_value))

            p1, p2, p3, p4 = st.columns(4)
            initial_capital = p1.number_input(
                "Initial capital",
                min_value=1_000.0,
                value=float(loaded.initial_capital if loaded else 100_000),
                step=5_000.0,
            )
            allocation_pct = (
                p2.slider(
                    "Allocation per position",
                    1,
                    100,
                    int((loaded.allocation_pct if loaded else 0.10) * 100),
                )
                / 100
            )
            stop_loss = (
                p3.number_input(
                    "Stop loss % (0=off)",
                    min_value=0.0,
                    value=float((loaded.stop_loss_pct or 0) * 100 if loaded else 2.0),
                    step=0.25,
                )
                / 100
            )
            take_profit = (
                p4.number_input(
                    "Take profit % (0=off)",
                    min_value=0.0,
                    value=float((loaded.take_profit_pct or 0) * 100 if loaded else 4.0),
                    step=0.25,
                )
                / 100
            )
            commission = st.number_input(
                "Commission per side",
                min_value=0.0,
                value=float(loaded.commission_per_trade if loaded else 0.0),
                step=0.25,
            )
            save_col, run_col = st.columns(2)
            save_clicked = save_col.form_submit_button("Save strategy")
            run_clicked = run_col.form_submit_button("Run backtest", type="primary")

        definition = StrategyDefinition(
            name=strategy_name.strip() or "Untitled Strategy",
            description=description.strip(),
            entry_rules=tuple(entry_rules),
            exit_rules=tuple(exit_rules),
            initial_capital=float(initial_capital),
            allocation_pct=float(allocation_pct),
            commission_per_trade=float(commission),
            stop_loss_pct=None if stop_loss == 0 else float(stop_loss),
            take_profit_pct=None if take_profit == 0 else float(take_profit),
        )
        if save_clicked:
            repository.save(definition)
            st.success(f"Saved strategy: {definition.name}")
        if run_clicked:
            st.session_state.backtest_result = BacktestEngine().run(
                definition, controller.all_histories()
            )
            st.session_state.backtest_definition = definition
            st.success("Backtest complete. Open Backtest results.")

        if saved_strategies:
            delete_name = st.selectbox(
                "Delete strategy", ["—"] + sorted(saved_strategies), key="delete_strategy"
            )
            if st.button("Delete selected strategy", disabled=delete_name == "—"):
                repository.delete(delete_name)
                st.rerun()

    with results_tab:
        result = st.session_state.get("backtest_result")
        if result is None:
            st.info(
                "Build a strategy and run a backtest first. Simulator mode produces the richest local history."
            )
        else:
            metrics = result.metrics
            m = st.columns(7)
            m[0].metric("Final equity", f"${metrics.final_equity:,.2f}")
            m[1].metric("Total return", f"{metrics.total_return:+.2%}")
            m[2].metric("Trades", metrics.trade_count)
            m[3].metric("Win rate", f"{metrics.win_rate:.1%}")
            m[4].metric(
                "Profit factor",
                "n/a"
                if metrics.profit_factor is None
                else (
                    "∞" if metrics.profit_factor == float("inf") else f"{metrics.profit_factor:.2f}"
                ),
            )
            m[5].metric("Max drawdown", f"{metrics.max_drawdown:.2%}")
            m[6].metric(
                "Sharpe", "n/a" if metrics.sharpe_ratio is None else f"{metrics.sharpe_ratio:.2f}"
            )
            if result.warnings:
                for warning in result.warnings:
                    st.warning(warning)
            equity_df = pd.DataFrame(
                [
                    {"datetime": point.timestamp, "equity": point.equity}
                    for point in result.equity_curve
                ]
            )
            if not equity_df.empty:
                st.plotly_chart(
                    px.line(equity_df, x="datetime", y="equity", title="Equity curve"),
                    use_container_width=True,
                )
            trades_df = pd.DataFrame(
                [
                    {
                        "symbol": trade.symbol,
                        "entry_time": trade.entry_time,
                        "exit_time": trade.exit_time,
                        "entry_price": trade.entry_price,
                        "exit_price": trade.exit_price,
                        "quantity": trade.quantity,
                        "pnl": trade.pnl,
                        "return_pct": trade.return_pct * 100,
                        "exit_reason": trade.exit_reason,
                    }
                    for trade in result.trades
                ]
            )
            st.markdown("#### Trade list")
            if trades_df.empty:
                st.info("No entries were generated by these rules over the loaded history.")
            else:
                st.dataframe(
                    trades_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "entry_price": st.column_config.NumberColumn(format="$%.2f"),
                        "exit_price": st.column_config.NumberColumn(format="$%.2f"),
                        "pnl": st.column_config.NumberColumn(format="$%.2f"),
                        "return_pct": st.column_config.NumberColumn("Return %", format="%+.2f%%"),
                    },
                )

    with paper_tab:
        prices = {record.symbol: record.price for record in records}
        portfolio.mark(prices)
        snap = portfolio.snapshot()
        pc = st.columns(5)
        pc[0].metric("Paper equity", f"${snap.equity:,.2f}")
        pc[1].metric("Cash", f"${snap.cash:,.2f}")
        pc[2].metric("Market value", f"${snap.market_value:,.2f}")
        pc[3].metric("Realized P&L", f"${snap.realized_pnl:+,.2f}")
        pc[4].metric("Unrealized P&L", f"${snap.unrealized_pnl:+,.2f}")
        if records:
            trade_symbols = [record.symbol for record in records]
            selected_trade_symbol = st.selectbox(
                "Symbol",
                trade_symbols,
                index=trade_symbols.index(st.session_state.selected_symbol)
                if st.session_state.get("selected_symbol") in trade_symbols
                else 0,
            )
            selected_price = prices[selected_trade_symbol]
            o1, o2, o3, o4 = st.columns(4)
            side = o1.selectbox("Side", ["BUY", "SELL"])
            quantity = int(o2.number_input("Quantity", min_value=1, value=10, step=1))
            o3.metric("Reference price", f"${selected_price:,.2f}")
            note = o4.text_input("Journal note", value="Manual Strategy Lab order")
            if st.button("Place paper order", type="primary"):
                try:
                    if side == "BUY":
                        portfolio.buy(selected_trade_symbol, quantity, selected_price, note)
                    else:
                        portfolio.sell(selected_trade_symbol, quantity, selected_price, note)
                    st.success(
                        f"Paper {side} filled: {quantity} {selected_trade_symbol} @ ${selected_price:.2f}"
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.info("Refresh market data before placing paper orders.")

        positions_df = pd.DataFrame(
            [
                {
                    "symbol": item.symbol,
                    "quantity": item.quantity,
                    "average_price": item.average_price,
                    "last_price": item.last_price,
                    "market_value": item.market_value,
                    "unrealized_pnl": item.unrealized_pnl,
                }
                for item in snap.positions
            ]
        )
        st.markdown("#### Positions")
        if positions_df.empty:
            st.caption("No paper positions.")
        else:
            st.dataframe(positions_df, use_container_width=True, hide_index=True)
        journal_df = pd.DataFrame(
            [
                {
                    "timestamp": item.timestamp,
                    "symbol": item.symbol,
                    "side": item.side.value,
                    "quantity": item.quantity,
                    "price": item.price,
                    "realized_pnl": item.realized_pnl,
                    "note": item.note,
                }
                for item in reversed(snap.journal)
            ]
        )
        st.markdown("#### Trade journal")
        if journal_df.empty:
            st.caption("No paper trades.")
        else:
            st.dataframe(journal_df, use_container_width=True, hide_index=True)


elif page == "Research Lab":
    st.subheader("Research & Optimization Lab")
    st.caption(
        "Run deterministic grid searches, walk-forward validation, Monte Carlo analysis, and save reproducible experiments."
    )

    if "strategy_repository" not in st.session_state:
        st.session_state.strategy_repository = YamlStrategyRepository(
            ROOT / "data/saved_strategies.yaml"
        )
    research_repository = SqliteExperimentRepository(ROOT / "data/research_experiments.sqlite3")
    saved_research_strategies = {
        item.name: item for item in st.session_state.strategy_repository.list()
    }

    if not saved_research_strategies:
        st.info("Save a strategy in Strategy Lab before using Research Lab.")
    else:
        strategy_name = st.selectbox(
            "Research strategy", sorted(saved_research_strategies), key="research_strategy"
        )
        research_definition = saved_research_strategies[strategy_name]
        histories = controller.all_histories()
        optimizer_tab, walk_tab, monte_tab, scorecard_tab, experiments_tab = st.tabs(
            ["Optimizer", "Walk forward", "Monte Carlo", "Scorecard & Compare", "Experiments"]
        )

        with optimizer_tab:
            st.markdown("#### Grid-search risk parameters")
            c1, c2, c3 = st.columns(3)
            objective = OptimizationObjective(
                c1.selectbox("Objective", [item.value for item in OptimizationObjective])
            )
            stop_values = c2.text_input("Stop loss values (%)", "1,2,3")
            target_values = c3.text_input("Take profit values (%)", "2,4,6")
            allocation_values = st.text_input("Allocation values (%)", "5,10,20")

            def parse_percentages(raw: str) -> tuple[float, ...]:
                return tuple(
                    float(value.strip()) / 100.0 for value in raw.split(",") if value.strip()
                )

            if st.button("Run optimization", type="primary"):
                try:
                    ranges = (
                        ParameterRange("stop_loss_pct", parse_percentages(stop_values)),
                        ParameterRange("take_profit_pct", parse_percentages(target_values)),
                        ParameterRange("allocation_pct", parse_percentages(allocation_values)),
                    )
                    with st.spinner("Evaluating parameter combinations..."):
                        optimized = GridSearchOptimizer().run(
                            research_definition, histories, ranges, objective
                        )
                    st.session_state.optimization_result = optimized
                    st.success(f"Optimization complete: {len(optimized.trials)} trials")
                except ValueError as exc:
                    st.error(str(exc))

            optimized = st.session_state.get("optimization_result")
            if optimized is not None:
                trial_rows = []
                for index, trial in enumerate(optimized.trials, start=1):
                    trial_rows.append(
                        {
                            "rank": index,
                            **{key: value * 100 for key, value in trial.parameters.items()},
                            "score": trial.score,
                            "return_pct": trial.result.metrics.total_return * 100,
                            "sharpe": trial.result.metrics.sharpe_ratio,
                            "max_drawdown_pct": trial.result.metrics.max_drawdown * 100,
                            "trades": trial.result.metrics.trade_count,
                        }
                    )
                trials_df = pd.DataFrame(trial_rows)
                st.dataframe(trials_df, use_container_width=True, hide_index=True)
                robustness = analyze_robustness(optimized)
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Positive trials", f"{robustness.positive_ratio:.0%}")
                r2.metric("Stability score", robustness.stability_score)
                r3.metric(
                    "Mean score",
                    "n/a" if robustness.mean_score is None else f"{robustness.mean_score:.3f}",
                )
                r4.metric(
                    "Score dispersion",
                    "n/a" if robustness.score_stddev is None else f"{robustness.score_stddev:.3f}",
                )
                if {"stop_loss_pct", "take_profit_pct", "score"}.issubset(trials_df.columns):
                    heatmap_df = trials_df.pivot_table(
                        index="take_profit_pct",
                        columns="stop_loss_pct",
                        values="score",
                        aggfunc="mean",
                    )
                    heatmap = px.imshow(
                        heatmap_df,
                        text_auto=".2f",
                        aspect="auto",
                        title="Parameter stability heatmap",
                        labels={"x": "Stop loss %", "y": "Take profit %", "color": "Score"},
                    )
                    st.plotly_chart(heatmap, use_container_width=True)
                best = optimized.best_trial
                if best is not None:
                    b1, b2, b3, b4 = st.columns(4)
                    b1.metric("Best score", f"{best.score:.4f}")
                    b2.metric("Return", f"{best.result.metrics.total_return:+.2%}")
                    b3.metric(
                        "Sharpe",
                        "n/a"
                        if best.result.metrics.sharpe_ratio is None
                        else f"{best.result.metrics.sharpe_ratio:.2f}",
                    )
                    b4.metric("Max drawdown", f"{best.result.metrics.max_drawdown:.2%}")
                    notes = st.text_input("Experiment notes", key="optimization_notes")
                    if st.button("Save best experiment"):
                        metrics = best.result.metrics
                        experiment = ResearchExperiment(
                            None,
                            f"{strategy_name} optimization",
                            datetime.now(UTC),
                            research_definition,
                            optimized.objective.value,
                            best.parameters,
                            {
                                "total_return": metrics.total_return,
                                "sharpe_ratio": metrics.sharpe_ratio,
                                "max_drawdown": metrics.max_drawdown,
                                "profit_factor": metrics.profit_factor,
                                "trade_count": metrics.trade_count,
                            },
                            notes,
                        )
                        experiment_id = research_repository.save(experiment)
                        st.success(f"Saved experiment #{experiment_id}")

        with walk_tab:
            st.markdown("#### Rolling out-of-sample validation")
            w1, w2, w3 = st.columns(3)
            folds = int(w1.number_input("Folds", min_value=1, max_value=10, value=3))
            train_fraction = w2.slider("Initial training fraction", 0.4, 0.8, 0.6, 0.05)
            wf_objective = OptimizationObjective(
                w3.selectbox(
                    "Walk-forward objective", [item.value for item in OptimizationObjective]
                )
            )
            if st.button("Run walk-forward"):
                ranges = (
                    ParameterRange("stop_loss_pct", (0.01, 0.02, 0.03)),
                    ParameterRange("take_profit_pct", (0.02, 0.04, 0.06)),
                )
                with st.spinner("Training and validating folds..."):
                    st.session_state.walk_forward_result = WalkForwardEngine().run(
                        research_definition,
                        histories,
                        ranges,
                        train_fraction,
                        folds,
                        wf_objective,
                    )
            wf = st.session_state.get("walk_forward_result")
            if wf is not None:
                w1, w2 = st.columns(2)
                w1.metric("Compounded OOS return", f"{wf.combined_return:+.2%}")
                w2.metric("Average fold return", f"{wf.average_out_of_sample_return:+.2%}")
                rows = [
                    {
                        "fold": fold.fold,
                        "train": f"{fold.train_start:%Y-%m-%d %H:%M} → {fold.train_end:%Y-%m-%d %H:%M}",
                        "test": f"{fold.test_start:%Y-%m-%d %H:%M} → {fold.test_end:%Y-%m-%d %H:%M}",
                        "parameters": fold.selected_parameters,
                        "in_sample_score": fold.in_sample_score,
                        "oos_return_pct": fold.out_of_sample_result.metrics.total_return * 100,
                        "oos_trades": fold.out_of_sample_result.metrics.trade_count,
                    }
                    for fold in wf.folds
                ]
                wf_df = pd.DataFrame(rows)
                st.dataframe(wf_df, use_container_width=True, hide_index=True)
                if not wf_df.empty:
                    fold_chart = px.bar(
                        wf_df,
                        x="fold",
                        y="oos_return_pct",
                        title="Out-of-sample return by fold",
                        labels={"oos_return_pct": "OOS return %"},
                    )
                    fold_chart.add_hline(y=0, line_dash="dash")
                    st.plotly_chart(fold_chart, use_container_width=True)

        with monte_tab:
            st.markdown("#### Trade-sequence Monte Carlo")
            base_result = st.session_state.get("backtest_result")
            if base_result is None:
                st.info("Run a backtest in Strategy Lab first.")
            else:
                simulations = int(st.number_input("Simulations", 100, 20_000, 1_000, 100))
                seed = int(st.number_input("Random seed", 0, 1_000_000, 7))
                if st.button("Run Monte Carlo"):
                    st.session_state.monte_carlo_result = MonteCarloEngine().run(
                        base_result, simulations, seed
                    )
                monte = st.session_state.get("monte_carlo_result")
                if monte is not None:
                    mc = st.columns(5)
                    mc[0].metric("Median equity", f"${monte.median_final_equity:,.2f}")
                    mc[1].metric("5th percentile", f"${monte.percentile_5_final_equity:,.2f}")
                    mc[2].metric("95th percentile", f"${monte.percentile_95_final_equity:,.2f}")
                    mc[3].metric("Loss probability", f"{monte.probability_of_loss:.1%}")
                    mc[4].metric("Median max DD", f"{monte.median_max_drawdown:.2%}")
                    st.plotly_chart(
                        px.histogram(
                            pd.DataFrame({"final_equity": monte.final_equities}),
                            x="final_equity",
                            nbins=40,
                            title="Monte Carlo final-equity distribution",
                        ),
                        use_container_width=True,
                    )
                    extended = extended_metrics(base_result)
                    st.markdown("#### Extended performance metrics")
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "annualized_return": extended.annualized_return,
                                    "annualized_volatility": extended.annualized_volatility,
                                    "sortino_ratio": extended.sortino_ratio,
                                    "calmar_ratio": extended.calmar_ratio,
                                    "recovery_factor": extended.recovery_factor,
                                    "payoff_ratio": extended.payoff_ratio,
                                    "average_holding_hours": extended.average_holding_hours,
                                }
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

        with scorecard_tab:
            st.markdown("#### Deployment readiness scorecard")
            base_result = st.session_state.get("backtest_result")
            if base_result is None:
                st.info("Run a backtest in Strategy Lab to generate a deployment scorecard.")
            else:
                scorecard = ScorecardEngine().evaluate(base_result)
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Readiness", scorecard.status.value)
                s2.metric("Score", f"{scorecard.score}/100")
                s3.metric("Return", f"{scorecard.total_return:+.2%}")
                s4.metric("Max drawdown", f"{scorecard.max_drawdown:.2%}")
                checks_df = pd.DataFrame(
                    [
                        {"check": name.replace("_", " ").title(), "passed": passed}
                        for name, passed in scorecard.checks.items()
                    ]
                )
                st.dataframe(checks_df, use_container_width=True, hide_index=True)
                if scorecard.reasons:
                    st.warning("Review required: " + ", ".join(scorecard.reasons))
                else:
                    st.success("All paper-deployment gates passed.")

                comparison_results = [base_result]
                optimized = st.session_state.get("optimization_result")
                if optimized is not None and optimized.best_trial is not None:
                    comparison_results.append(optimized.best_trial.result)
                comparison = compare_strategies(comparison_results)
                st.markdown("#### Strategy comparison")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "strategy": row.strategy_name,
                                "total_return_pct": row.total_return * 100,
                                "max_drawdown_pct": row.max_drawdown * 100,
                                "sharpe": row.sharpe_ratio,
                                "sortino": row.sortino_ratio,
                                "profit_factor": row.profit_factor,
                                "win_rate_pct": row.win_rate * 100,
                                "trades": row.trade_count,
                            }
                            for row in comparison
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

        with experiments_tab:
            st.markdown("#### Persistent experiment journal")
            experiments = research_repository.list()
            if not experiments:
                st.caption("No experiments saved yet.")
            else:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "id": item.id,
                                "created_at": item.created_at,
                                "name": item.name,
                                "strategy": item.strategy.name,
                                "objective": item.objective,
                                "parameters": item.parameters,
                                "metrics": item.metrics,
                                "notes": item.notes,
                            }
                            for item in experiments
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

elif page == "Execution":
    st.subheader("Execution Platform")
    st.caption(
        "Risk-gated local paper execution and explicitly armed IBKR paper trading. Live-account ports are blocked by design."
    )

    prices = {record.symbol: record.price for record in records}
    broker_mode = st.radio("Execution broker", ["Local Paper", "IBKR Paper"], horizontal=True)

    with st.expander("Risk controls", expanded=True):
        r1, r2, r3, r4 = st.columns(4)
        max_order_notional = r1.number_input(
            "Max order notional", min_value=100.0, value=10_000.0, step=500.0
        )
        max_position_notional = r2.number_input(
            "Max position notional", min_value=100.0, value=25_000.0, step=1_000.0
        )
        max_daily_loss = r3.number_input(
            "Daily loss limit", min_value=100.0, value=1_000.0, step=100.0
        )
        max_open_orders = int(r4.number_input("Max open orders", min_value=0, value=10, step=1))
        r5, r6, r7 = st.columns(3)
        max_symbol_quantity = int(
            r5.number_input("Max symbol quantity", min_value=1, value=1_000, step=10)
        )
        allow_short = r6.toggle("Allow short selling", value=False)
        kill_switch = r7.toggle(
            "Kill switch", value=False, help="Reject every new order immediately"
        )
    limits = RiskLimits(
        max_order_notional=float(max_order_notional),
        max_position_notional=float(max_position_notional),
        max_daily_loss=float(max_daily_loss),
        max_open_orders=max_open_orders,
        max_symbol_quantity=max_symbol_quantity,
        allow_short_selling=allow_short,
        kill_switch=kill_switch,
    )

    journal_path = ROOT / "data/execution_journal.sqlite3"
    if "execution_journal" not in st.session_state:
        st.session_state.execution_journal = SQLiteTradeJournal(journal_path)
    journal = st.session_state.execution_journal

    manager = None
    if broker_mode == "Local Paper":
        if "paper_execution_broker" not in st.session_state:
            broker = PaperExecutionBroker(100_000.0)
            broker.connect()
            st.session_state.paper_execution_broker = broker
        broker = st.session_state.paper_execution_broker
        manager = OrderManager(broker, journal)
        st.success("Local paper broker connected")
    else:
        st.warning(
            "IBKR orders can affect your paper account. Confirm TWS/IB Gateway is logged into PAPER and API access is enabled."
        )
        ib = settings.market_data.ibkr
        c1, c2, c3 = st.columns(3)
        host = c1.text_input("IBKR host", value=ib.host)
        port = int(
            c2.number_input(
                "Paper port",
                value=int(ib.port),
                step=1,
                help="TWS paper: 7497; Gateway paper: 4002",
            )
        )
        client_id = int(
            c3.number_input("Execution client ID", value=int(ib.client_id) + 100, step=1)
        )
        confirm = st.text_input("Type PAPER to arm IBKR execution")
        armed = st.toggle("Arm IBKR paper order routing", value=False)
        connect_col, disconnect_col = st.columns(2)
        if connect_col.button("Connect IBKR paper", disabled=not (armed and confirm == "PAPER")):
            try:
                old = st.session_state.pop("ibkr_execution_broker", None)
                if old is not None:
                    old.disconnect()
                broker = IBKRPaperBroker(host, port, client_id, paper_only=True)
                broker.connect()
                st.session_state.ibkr_execution_broker = broker
                st.success("Connected to IBKR paper execution")
            except Exception as exc:
                st.error(str(exc))
        if disconnect_col.button("Disconnect IBKR paper"):
            broker = st.session_state.pop("ibkr_execution_broker", None)
            if broker is not None:
                broker.disconnect()
            st.info("IBKR execution disconnected")
        broker = st.session_state.get("ibkr_execution_broker")
        if broker is not None:
            manager = OrderManager(broker, journal)
            st.success("IBKR paper broker connected and armed for this session")
        else:
            st.info("IBKR paper execution is not connected. Order ticket remains disabled.")

    account = None
    if manager is not None:
        try:
            account = manager.broker.account_snapshot(prices)
            a = st.columns(6)
            a[0].metric("Account", account.account_id)
            a[1].metric("Net liquidation", f"${account.net_liquidation:,.2f}")
            a[2].metric("Cash", f"${account.cash:,.2f}")
            a[3].metric("Buying power", f"${account.buying_power:,.2f}")
            a[4].metric("Realized P&L", f"${account.realized_pnl:+,.2f}")
            a[5].metric("Unrealized P&L", f"${account.unrealized_pnl:+,.2f}")
        except Exception as exc:
            st.error(f"Account synchronization failed: {exc}")
            account = None

    st.markdown("#### Order ticket")
    if records and manager is not None and account is not None:
        available_symbols = [record.symbol for record in records]
        selected = st.selectbox(
            "Order symbol",
            available_symbols,
            index=available_symbols.index(st.session_state.selected_symbol)
            if st.session_state.get("selected_symbol") in available_symbols
            else 0,
        )
        reference_price = prices[selected]
        t1, t2, t3, t4 = st.columns(4)
        order_side = ExecutionSide(t1.selectbox("Side", [item.value for item in ExecutionSide]))
        order_type = ExecutionOrderType(
            t2.selectbox("Order type", [item.value for item in ExecutionOrderType])
        )
        quantity = int(t3.number_input("Quantity", min_value=1, value=10, step=1))
        t4.metric("Reference price", f"${reference_price:,.2f}")
        p1, p2 = st.columns(2)
        limit_price = p1.number_input(
            "Limit price",
            min_value=0.01,
            value=float(reference_price),
            step=0.01,
            disabled=order_type is not ExecutionOrderType.LIMIT,
        )
        stop_price = p2.number_input(
            "Stop price",
            min_value=0.01,
            value=float(reference_price),
            step=0.01,
            disabled=order_type is not ExecutionOrderType.STOP,
        )
        note = st.text_input("Order note", value="Manual terminal order")
        estimated_notional = reference_price * quantity
        st.caption(f"Estimated notional: ${estimated_notional:,.2f}")
        if st.button("Submit risk-checked order", type="primary"):
            request = OrderRequest(
                symbol=selected,
                side=order_side,
                quantity=quantity,
                order_type=order_type,
                limit_price=float(limit_price) if order_type is ExecutionOrderType.LIMIT else None,
                stop_price=float(stop_price) if order_type is ExecutionOrderType.STOP else None,
                reference_price=float(reference_price),
                strategy="manual-terminal",
                note=note,
            )
            order = manager.submit(request, limits, prices)
            if order.status.value in {"REJECTED", "ERROR"}:
                st.error(f"{order.status.value}: {order.message}")
            else:
                st.success(
                    f"{order.status.value}: {order.request.quantity} {order.request.symbol} · {order.message}"
                )
                st.rerun()
    else:
        st.info("Load market data and connect an execution broker to enable the order ticket.")

    if account is not None:
        position_rows = [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "average_cost": p.average_cost,
                "market_price": p.market_price,
                "market_value": p.market_value,
                "unrealized_pnl": p.unrealized_pnl,
            }
            for p in account.positions
        ]
        st.markdown("#### Broker positions")
        if position_rows:
            st.dataframe(pd.DataFrame(position_rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No broker positions.")

    st.markdown("#### Order management and audit journal")
    orders = journal.recent_orders(100)
    order_rows = [
        {
            "submitted_at": o.submitted_at,
            "order_id": o.order_id,
            "broker_order_id": o.broker_order_id,
            "mode": o.mode.value,
            "symbol": o.request.symbol,
            "side": o.request.side.value,
            "quantity": o.request.quantity,
            "type": o.request.order_type.value,
            "status": o.status.value,
            "fill_price": o.average_fill_price,
            "message": o.message,
        }
        for o in orders
    ]
    if order_rows:
        st.dataframe(pd.DataFrame(order_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No execution orders have been journaled.")
    fills = journal.recent_fills(100)
    fill_rows = [
        {
            "timestamp": f.timestamp,
            "fill_id": f.fill_id,
            "order_id": f.order_id,
            "symbol": f.symbol,
            "side": f.side.value,
            "quantity": f.quantity,
            "price": f.price,
            "commission": f.commission,
        }
        for f in fills
    ]
    st.markdown("#### Trade fills")
    if fill_rows:
        st.dataframe(pd.DataFrame(fill_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No fills recorded.")

elif page == "Automation":
    st.subheader("Strategy Automation")
    st.caption(
        "Guarded paper-only orchestration. Start in DRY_RUN; PAPER_ARMED routes only to the local paper broker in this release."
    )
    strategy_repo = YamlStrategyRepository(ROOT / "data/saved_strategies.yaml")
    strategies = strategy_repo.list()
    if not strategies:
        st.info("Save at least one strategy in Strategy Lab before running automation.")
    elif not records:
        st.info("Load market data before running an automation cycle.")
    else:
        names = [item.name for item in strategies]
        selected_name = st.selectbox("Saved strategy", names)
        selected_strategy = next(item for item in strategies if item.name == selected_name)
        mode = AutomationMode(
            st.radio("Mode", [item.value for item in AutomationMode], horizontal=True, index=1)
        )
        a1, a2, a3, a4 = st.columns(4)
        quantity = int(a1.number_input("Quantity", min_value=1, value=10, step=1))
        max_orders = int(a2.number_input("Max orders/cycle", min_value=0, value=3, step=1))
        max_positions = int(a3.number_input("Max open positions", min_value=0, value=5, step=1))
        cooldown = int(a4.number_input("Cooldown seconds", min_value=0, value=300, step=30))
        positive_guard = st.toggle("Require positive ROC for entries", value=True)
        confirm = st.text_input("Type AUTOMATE to enable PAPER_ARMED", value="")
        armed_ok = mode is not AutomationMode.PAPER_ARMED or confirm == "AUTOMATE"
        if mode is AutomationMode.PAPER_ARMED and not armed_ok:
            st.warning("PAPER_ARMED remains locked until AUTOMATE is typed exactly.")
        if "automation_paper_broker" not in st.session_state:
            auto_broker = PaperExecutionBroker(100_000.0)
            auto_broker.connect()
            st.session_state.automation_paper_broker = auto_broker
        auto_journal = SQLiteTradeJournal(ROOT / "data/automation_execution.sqlite3")
        auto_manager = OrderManager(st.session_state.automation_paper_broker, auto_journal)
        run_journal = JsonlAutomationJournal(ROOT / "data/automation_runs.jsonl")
        config = AutomationConfig(
            mode=mode,
            quantity=quantity,
            max_orders_per_cycle=max_orders,
            max_open_positions=max_positions,
            cooldown_seconds=cooldown,
            require_positive_roc=positive_guard,
        )
        limits = RiskLimits()
        if st.button("Run one guarded automation cycle", type="primary", disabled=not armed_ok):
            runner = st.session_state.get("automation_runner")
            if runner is None:
                runner = AutomationRunner(auto_manager, run_journal)
                st.session_state.automation_runner = runner
            result = runner.run_cycle(selected_strategy, list(records), config, limits)
            st.session_state.last_automation_run = result
        result = st.session_state.get("last_automation_run")
        if result is not None:
            st.markdown("#### Latest cycle")
            st.write(
                f"**{result.strategy_name}** · {result.mode.value} · evaluated {result.evaluated} symbols"
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "symbol": d.symbol,
                            "action": d.action,
                            "reason": d.reason,
                            "submitted": d.submitted,
                            "order_id": d.order_id,
                        }
                        for d in result.decisions
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        st.markdown("#### Automation audit")
        recent_runs = run_journal.recent(25)
        if recent_runs:
            st.dataframe(pd.DataFrame(recent_runs), use_container_width=True, hide_index=True)
        else:
            st.caption("No automation cycles journaled yet.")

elif page == "Scheduler & Alerts":
    st.subheader("Automation Scheduler & Alert Center")
    st.caption(
        "Session-aware scheduling, persistent operator state, failure shutdown, and deduplicated local alerts."
    )

    if "notification_memory" not in st.session_state:
        st.session_state.notification_memory = InMemoryNotificationSink()
    if "notification_router" not in st.session_state:
        st.session_state.notification_router = NotificationRouter(
            [
                st.session_state.notification_memory,
                JsonlNotificationSink(ROOT / "data/notifications.jsonl"),
            ],
            cooldown_seconds=60,
        )
    if "automation_state_store" not in st.session_state:
        st.session_state.automation_state_store = SQLiteAutomationStateStore(
            ROOT / "data/automation_state.sqlite3"
        )

    state_store = st.session_state.automation_state_store
    c1, c2, c3, c4 = st.columns(4)
    interval = int(c1.number_input("Cycle interval (sec)", min_value=5, value=60, step=5))
    failure_limit = int(c2.number_input("Failure shutdown threshold", min_value=1, value=3, step=1))
    session_start = c3.time_input("Session start", value=pd.Timestamp("09:30").time())
    session_end = c4.time_input("Session end", value=pd.Timestamp("16:00").time())
    timezone_name = st.text_input("Session timezone", value="America/New_York")

    if "scheduler_cycle_counter" not in st.session_state:
        st.session_state.scheduler_cycle_counter = 0

    def scheduled_cycle() -> None:
        st.session_state.scheduler_cycle_counter += 1
        state_store.set("cycle_counter", st.session_state.scheduler_cycle_counter)
        state_store.set("last_cycle_source", source)
        state_store.set("last_cycle_symbols", symbols)

    requested_config = SchedulerConfig(
        interval_seconds=interval,
        max_consecutive_failures=failure_limit,
        session_policy=MarketSessionPolicy(
            timezone_name=timezone_name,
            start_time=session_start,
            end_time=session_end,
        ),
    )
    scheduler_signature = (
        interval,
        failure_limit,
        timezone_name,
        session_start.isoformat(),
        session_end.isoformat(),
    )
    if st.session_state.get("scheduler_signature") != scheduler_signature:
        st.session_state.scheduler_signature = scheduler_signature
        st.session_state.automation_scheduler = AutomationScheduler(
            requested_config,
            scheduled_cycle,
            st.session_state.notification_router,
        )
    scheduler = st.session_state.automation_scheduler

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("Start", type="primary", use_container_width=True):
        scheduler.start()
        state_store.set("operator_state", "RUNNING")
    if b2.button("Run due cycle", use_container_width=True):
        ran = scheduler.run_due()
        st.toast("Cycle completed" if ran else scheduler.status().last_message)
    if b3.button("Pause / Resume", use_container_width=True):
        if scheduler.status().paused:
            scheduler.resume()
            state_store.set("operator_state", "RUNNING")
        else:
            scheduler.pause()
            state_store.set("operator_state", "PAUSED")
    if b4.button("Stop", use_container_width=True):
        scheduler.stop()
        state_store.set("operator_state", "STOPPED")

    status = scheduler.status()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scheduler", "RUNNING" if status.running else "STOPPED")
    m2.metric("Paused", "YES" if status.paused else "NO")
    m3.metric("Cycles", int(state_store.get("cycle_counter", 0)))
    m4.metric("Failures", status.consecutive_failures)
    st.write(status.last_message)
    st.caption(f"Next run: {status.next_run_at or 'n/a'} · Last run: {status.last_run_at or 'n/a'}")

    st.markdown("#### Persistent operations state")
    st.json(
        {
            "operator_state": state_store.get("operator_state", "NOT_SET"),
            "cycle_counter": state_store.get("cycle_counter", 0),
            "last_cycle_source": state_store.get("last_cycle_source"),
            "last_cycle_symbols": state_store.get("last_cycle_symbols", []),
        }
    )

    st.markdown("#### Notification center")
    notifications = st.session_state.notification_memory.items
    if notifications:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "created_at": item.created_at,
                        "severity": item.severity.value,
                        "category": item.category,
                        "symbol": item.symbol,
                        "title": item.title,
                        "message": item.message,
                    }
                    for item in notifications
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No operational notifications yet.")
    st.info(
        "Sprint 8 scheduler is intentionally single-process and operator-driven. It does not create unattended IBKR sessions."
    )

elif page == "Market":
    st.subheader("Market analytics")
    breadth_cols = st.columns(5)
    breadth_cols[0].metric("Advancers", stats.advancers)
    breadth_cols[1].metric("Decliners", stats.decliners)
    breadth_cols[2].metric("Unchanged", stats.unchanged)
    breadth_cols[3].metric("Above VWAP", stats.above_vwap)
    ratio = stats.advancers / max(1, stats.decliners)
    breadth_cols[4].metric("A/D ratio", f"{ratio:.2f}")

    left, right = st.columns(2)
    valid = df.dropna(subset=["roc_pct"]) if not df.empty else df
    with left:
        st.markdown("#### Finviz-style treemap")
        if valid.empty:
            st.info("No ranked symbols yet.")
        else:
            treemap = valid.copy()
            treemap["tile_size"] = treemap["volume"].fillna(0).clip(lower=1)
            fig = px.treemap(
                treemap,
                path=["sector", "symbol"],
                values="tile_size",
                color="roc_pct",
                color_continuous_scale="RdYlGn",
                color_continuous_midpoint=0,
                hover_data={"price": ":.2f", "roc_pct": ":+.3f", "rvol": ":.2f"},
            )
            fig.update_layout(height=520, margin=dict(l=5, r=5, t=10, b=5))
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Sector ranking")
        sector_df = pd.DataFrame(controller.sectors())
        if sector_df.empty:
            st.info("No sector values yet.")
        else:
            sector_df["average_roc_pct"] = sector_df.average_roc * 100
            fig = px.bar(
                sector_df.sort_values("average_roc_pct"),
                x="average_roc_pct",
                y="sector",
                orientation="h",
                hover_data=["symbols"],
            )
            fig.add_vline(x=0, line_dash="dash")
            fig.update_layout(height=520, xaxis_title="Average ROC %", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Complete market snapshot")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "price": st.column_config.NumberColumn(format="$%.2f"),
            "roc_pct": st.column_config.NumberColumn("ROC %", format="%+.3f%%"),
            "vwap_distance_pct": st.column_config.NumberColumn("VWAP distance %", format="%+.3f%%"),
            "gap_pct": st.column_config.NumberColumn("Gap %", format="%+.2f%%"),
        },
    )

elif page == "Replay & Ops":
    st.subheader("Historical replay and operational health")
    st.caption(
        "Record normalized factor history, replay it deterministically, and inspect runtime health."
    )

    if "ops_metrics" not in st.session_state:
        st.session_state.ops_metrics = MetricsRegistry()
    metrics = st.session_state.ops_metrics
    metrics.set("ranked_symbols", len(records), "symbols")
    metrics.set("history_points", sum(len(v) for v in controller.all_histories().values()), "ticks")

    monitor = HealthMonitor()
    monitor.register(
        "market-data snapshot",
        lambda: (
            (HealthStatus.HEALTHY, f"{len(records)} symbols available")
            if records
            else (HealthStatus.DEGRADED, "No market snapshot loaded")
        ),
    )
    monitor.register(
        "execution journal",
        lambda: (
            (HealthStatus.HEALTHY, "SQLite journal available")
            if (ROOT / "data").exists()
            else (HealthStatus.DEGRADED, "Data directory missing")
        ),
    )
    health_rows = [
        {
            "component": item.name,
            "status": item.status.value,
            "message": item.message,
            "latency_ms": item.latency_ms,
            "checked_at": item.checked_at,
        }
        for item in monitor.run()
    ]
    st.markdown("#### Component health")
    st.dataframe(pd.DataFrame(health_rows), use_container_width=True, hide_index=True)

    metric_rows = [
        {
            "metric": item.name,
            "value": item.value,
            "unit": item.unit,
            "recorded_at": item.recorded_at,
        }
        for item in metrics.snapshot()
    ]
    st.markdown("#### Runtime metrics")
    st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)

    st.markdown("#### Session recorder")
    replay_path = ROOT / "data" / "market_session.csv"
    left, right = st.columns(2)
    with left:
        if st.button("Save current history", use_container_width=True):
            ticks = []
            for symbol, history in controller.all_histories().items():
                ticks.extend(
                    Tick(symbol, row.timestamp, row.price, row.volume, "recorded")
                    for row in history
                )
            count = CsvTickStore().save(replay_path, ticks)
            metrics.increment("sessions_recorded")
            st.success(f"Saved {count:,} normalized ticks to {replay_path.relative_to(ROOT)}")
    with right:
        if st.button(
            "Replay saved session", use_container_width=True, disabled=not replay_path.exists()
        ):
            loaded = CsvTickStore().load(replay_path)
            replay_controller = DashboardController(symbols, lookback)
            result = ReplayEngine().replay(loaded, replay_controller.ingest, batch_size=500)
            st.session_state.controller = replay_controller
            metrics.increment("replayed_ticks", result.processed, "ticks")
            st.success(
                f"Replayed {result.processed:,} ticks in event-time order. Reloading dashboard state."
            )
            st.rerun()

    st.info(
        "Replay uses normalized CSV ticks and does not place orders. It is safe for scanner and strategy validation."
    )

else:
    st.subheader("Sprint 8 architecture")
    st.code(
        """Yahoo / IBKR / Simulator adapters
              │
              ▼
        normalized Tick model
              │
              ▼
     ReactiveFactorEngine
  (ROC, RVOL, VWAP, gap, ORB)
              │
              ▼
 cross-sectional ranking + statistics
              │
              ▼
 DashboardController
              │
              ├── ScannerEngine + AlertEngine
              ├── Strategy rules + BacktestEngine
              ├── PaperPortfolio + trade journal
              │
              ▼
 thin Streamlit terminal
              ├── deterministic replay
              └── health + runtime metrics""",
        language="text",
    )
    st.markdown(
        "The UI renders application data only. Factor calculations, ranking, statistics, "
        "provider normalization, and selected-symbol history remain outside Streamlit."
    )
