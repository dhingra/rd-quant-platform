"""RD Quant Terminal — Sprint 2 streaming market dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rdqp.dashboard.application.controller import DashboardController
from rdqp.datasources.ibkr.snapshot import fetch_snapshot_ticks
from rdqp.datasources.yahoo.snapshot import fetch_latest_ticks
from rdqp.platform.config.settings import load_settings
from rdqp.scanners import FilterOperator, ScanDefinition, ScannerFilter, default_scans
from rdqp.scanners.infrastructure.yaml_repository import YamlScanRepository

st.set_page_config(page_title="RD Quant Platform", page_icon="📈", layout="wide")
settings = load_settings(ROOT / "config/app.yaml")


def parse_symbols(raw: str) -> list[str]:
    return list(dict.fromkeys(part.strip().upper() for part in raw.replace("\n", ",").split(",") if part.strip()))


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
    st.caption("Yahoo supplies delayed 1-minute bars. IBKR uses a read-only paper snapshot connection.")

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
        ticks = fetch_latest_ticks(symbols, settings.market_data.yahoo.period, settings.market_data.yahoo.interval)
        controller.ingest(ticks)
    else:
        ib = settings.market_data.ibkr
        ticks = fetch_snapshot_ticks(symbols, ib.host, ib.port, ib.client_id, ib.market_data_type)
        controller.ingest(ticks)


header_left, header_right = st.columns([5, 1])
with header_left:
    st.title("RD Quant Platform")
    st.caption("Sprint 3 · Scanner Engine · configurable filters → saved scans → alerts")
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
metric_cols[1].metric("Mean ROC", "n/a" if stats.mean_roc is None else f"{stats.mean_roc * 100:+.3f}%")
metric_cols[2].metric("Median ROC", "n/a" if stats.median_roc is None else f"{stats.median_roc * 100:+.3f}%")
metric_cols[3].metric("Std dev", "n/a" if stats.standard_deviation is None else f"{stats.standard_deviation * 100:.3f}%")
metric_cols[4].metric("Skew", "n/a" if stats.skew is None else f"{stats.skew:+.2f}")
metric_cols[5].metric("Positive", "n/a" if stats.positive_percentage is None else f"{stats.positive_percentage:.0%}")

page = st.segmented_control("View", ["Leaderboard", "Scanner", "Market", "Architecture"], default="Leaderboard")

if page == "Leaderboard":
    st.subheader("Live cross-sectional momentum")
    left, right = st.columns(2)
    display_cols = ["rank", "symbol", "sector", "price", "roc_pct", "rvol", "vwap_distance_pct", "orb"]
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
            st.session_state.selected_symbol = leaders.iloc[leader_event.selection.rows[0]]["symbol"]
    with right:
        st.markdown("#### Laggards")
        laggards = df.tail(leaderboard_size).sort_values("roc_pct")[display_cols] if not df.empty else df
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
            st.session_state.selected_symbol = laggards.iloc[laggard_event.selection.rows[0]]["symbol"]

    chart_left, chart_right = st.columns(2)
    valid = df.dropna(subset=["roc_pct"]) if not df.empty else df
    with chart_left:
        st.markdown("#### ROC distribution")
        if valid.empty:
            st.info("ROC needs enough event-time history for the selected lookback.")
        else:
            fig = px.histogram(valid, x="roc_pct", nbins=min(20, max(5, len(valid))), hover_data=["symbol"])
            fig.add_vline(x=0, line_dash="dash")
            fig.update_layout(xaxis_title="ROC %", yaxis_title="Symbols", height=340)
            st.plotly_chart(fig, use_container_width=True)
    with chart_right:
        st.markdown("#### Momentum breadth")
        positive = stats.positive_percentage * 100 if stats.positive_percentage is not None else 0
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=positive, number={"suffix": "%"},
            title={"text": "Symbols with positive ROC"}, gauge={"axis": {"range": [0, 100]}},
        ))
        gauge.update_layout(height=340, margin=dict(l=30, r=30, t=70, b=20))
        st.plotly_chart(gauge, use_container_width=True)

    st.divider()
    selected = st.session_state.get("selected_symbol")
    if selected and not df.empty and selected in set(df.symbol):
        st.subheader(f"Selected symbol · {selected}")
        selected_row = df[df.symbol == selected].iloc[0]
        cards = st.columns(6)
        cards[0].metric("Last", f"${selected_row.price:,.2f}")
        cards[1].metric("ROC", "n/a" if pd.isna(selected_row.roc_pct) else f"{selected_row.roc_pct:+.3f}%")
        cards[2].metric("Rank", int(selected_row["rank"]))
        cards[3].metric("RVOL", "n/a" if pd.isna(selected_row.rvol) else f"{selected_row.rvol:.2f}")
        cards[4].metric("VWAP distance", "n/a" if pd.isna(selected_row.vwap_distance_pct) else f"{selected_row.vwap_distance_pct:+.3f}%")
        cards[5].metric("ORB", selected_row.orb)

        history = controller.symbol_history(selected)
        history_df = pd.DataFrame({
            "datetime": [r.timestamp for r in history],
            "price": [r.price for r in history],
            "roc_pct": [None if r.roc is None else r.roc * 100 for r in history],
            "vwap": [r.vwap for r in history],
            "volume": [r.volume for r in history],
        })
        price_col, roc_col = st.columns(2)
        with price_col:
            price_chart = go.Figure()
            price_chart.add_trace(go.Scatter(x=history_df.datetime, y=history_df.price, name="Price"))
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
    st.caption("Composable filters run against the latest cross-sectional factor snapshot. Saved scans persist to data/saved_scans.yaml.")

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
        st.json({
            "sort_by": definition.sort_by,
            "descending": definition.descending,
            "limit": definition.limit,
            "filters": [
                {"field": f.field, "operator": f.operator.value, "value": f.value, "second_value": f.second_value}
                for f in definition.filters
            ],
        })

    result = controller.run_scan(definition)
    if alerts_enabled:
        new_alerts = controller.evaluate_alerts(result)
        st.session_state.scanner_alert_log = list(new_alerts) + st.session_state.scanner_alert_log[:99]

    summary_cols = st.columns(4)
    summary_cols[0].metric("Matches", len(result.matches))
    summary_cols[1].metric("Universe", result.evaluated_count)
    summary_cols[2].metric("Match rate", f"{len(result.matches) / max(1, result.evaluated_count):.1%}")
    summary_cols[3].metric("Scan latency", f"{result.elapsed_ms:.3f} ms")

    match_df = pd.DataFrame([match.values for match in result.matches])
    if match_df.empty:
        st.info("No symbols currently satisfy this scan.")
    else:
        visible = [c for c in ["rank", "symbol", "sector", "price", "roc_pct", "rvol", "gap_pct", "vwap_distance_pct", "opening_range_state", "volume"] if c in match_df.columns]
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
                "vwap_distance_pct": st.column_config.NumberColumn("VWAP distance %", format="%+.3f%%"),
                "rvol": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        if scan_event.selection.rows:
            selected_index = scan_event.selection.rows[0]
            st.session_state.selected_symbol = str(match_df.iloc[selected_index]["symbol"])
            st.success(f"Selected {st.session_state.selected_symbol}. Open Leaderboard to inspect its charts.")

    st.divider()
    builder, alert_panel = st.columns([3, 2])
    with builder:
        st.markdown("#### Build and save a custom scan")
        with st.form("custom_scan_form"):
            custom_name = st.text_input("Name", value="My Momentum Scan")
            custom_description = st.text_input("Description", value="Custom cross-sectional filter")
            field_options = ["roc_pct", "rvol", "gap_pct", "vwap_distance_pct", "price", "volume", "rank", "sector", "above_vwap", "orb_breakout", "orb_breakdown"]
            c1, c2, c3 = st.columns(3)
            custom_field = c1.selectbox("Field", field_options)
            boolean_field = custom_field in {"above_vwap", "orb_breakout", "orb_breakdown"}
            operators = [FilterOperator.IS_TRUE.value, FilterOperator.IS_FALSE.value] if boolean_field else [op.value for op in [FilterOperator.GTE, FilterOperator.GT, FilterOperator.LTE, FilterOperator.LT, FilterOperator.EQ, FilterOperator.NE]]
            custom_operator = c2.selectbox("Operator", operators)
            if custom_field == "sector":
                custom_value = c3.text_input("Value", value="Technology")
            elif boolean_field:
                custom_value = None
                c3.write("Boolean filter")
            else:
                custom_value = c3.number_input("Value", value=0.0, step=0.1, format="%.4f")
            sort_options = ["roc_pct", "rvol", "gap_pct", "vwap_distance_pct", "price", "volume", "rank"]
            s1, s2, s3 = st.columns(3)
            sort_by = s1.selectbox("Sort by", sort_options)
            descending = s2.toggle("Descending", value=True)
            scan_limit = s3.number_input("Limit", min_value=1, max_value=500, value=50)
            save_scan = st.form_submit_button("Save scan", type="primary")
        if save_scan:
            new_definition = ScanDefinition(
                name=custom_name.strip(),
                description=custom_description.strip(),
                filters=(ScannerFilter(custom_field, FilterOperator(custom_operator), custom_value),),
                sort_by=sort_by,
                descending=descending,
                limit=int(scan_limit),
            )
            repository.save(new_definition)
            st.success(f"Saved scan: {new_definition.name}")
            st.rerun()

        if saved:
            delete_name = st.selectbox("Delete saved scan", ["—"] + sorted(saved), key="delete_scan_name")
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
                treemap, path=["sector", "symbol"], values="tile_size", color="roc_pct",
                color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
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
                sector_df.sort_values("average_roc_pct"), x="average_roc_pct", y="sector",
                orientation="h", hover_data=["symbols"],
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

else:
    st.subheader("Sprint 3 architecture")
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
              │
              ▼
 thin Streamlit terminal""",
        language="text",
    )
    st.markdown(
        "The UI renders application data only. Factor calculations, ranking, statistics, "
        "provider normalization, and selected-symbol history remain outside Streamlit."
    )
