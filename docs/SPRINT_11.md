# Sprint 11 — Research Workstation

Sprint 11 adds UI-neutral analytics designed for interactive Streamlit and Plotly views.

## Capabilities

- Equity, drawdown, rolling Sharpe, and rolling volatility series
- Monthly return aggregation for heatmaps
- Trade filtering and win/loss/holding-time summaries
- Portfolio allocation and sector exposure analytics
- Deterministic replay playback state with play, pause, step, reset, and speed controls

The `rdqp.workstation` package keeps chart preparation and workstation state outside the UI layer so page modules can remain thin.
