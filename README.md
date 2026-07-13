# RD Quant Platform

**Version:** `0.5.0-alpha`  
**Release:** Sprint 5 — Execution Platform

RD Quant Platform is a modular, event-driven quantitative research and paper-trading platform inspired by the DolphinDB pattern of stateful per-symbol computation followed by cross-sectional analytics.

Sprint 5 is cumulative: it contains the architecture foundation, streaming dashboard, scanner engine, Strategy Lab, and execution platform developed in Sprints 1–5.

## Capabilities

### Sprint 1 — Architecture foundation

- ports-and-adapters architecture following SOLID principles
- immutable domain models and typed interfaces
- event bus, dependency injection, configuration, logging, and plugin registry
- independent Yahoo Finance, IBKR, and Simulator packages
- unit, integration, and CI test scaffolding

### Sprint 2 — Streaming market dashboard

- normalized Simulator, Yahoo, and IBKR market-data inputs
- event-time ROC, RVOL, VWAP distance, gap, and opening-range factors
- cross-sectional rankings, breadth, statistics, and sector strength
- ROC histogram, momentum gauge, Finviz-style treemap, and time-series charts
- shared clickable symbol selection across dashboard views

### Sprint 3 — Scanner engine

- composable scanner filters and configurable result sorting
- momentum, RVOL, gap, ORB, and VWAP preset scans
- custom scanner builder, YAML saved scans, and new-match alerts
- scanner latency and match-rate metrics

### Sprint 4 — Strategy Lab

- visual entry/exit rule builder and YAML saved strategies
- event-time backtesting with equity curve and detailed trade list
- return, win rate, profit factor, drawdown, expectancy, and Sharpe proxy
- isolated paper portfolio and research trade journal

### Sprint 5 — Execution platform

- broker-neutral order manager and execution ports
- deterministic local paper broker
- guarded IBKR paper broker for TWS `7497` and Gateway `4002` only
- synchronized account metrics and broker positions
- pre-trade risk controls: order/position limits, buying power, daily loss, open orders, shorting policy, and kill switch
- market, limit, and stop order tickets
- durable SQLite order/fill audit journal
- execution order management and fill views

## Architecture

```text
Yahoo / IBKR / Simulator
          │
          ▼
   normalized market events
          │
          ▼
 Reactive Factor Engine
 ROC · RVOL · VWAP · Gap · ORB
          │
          ▼
 Cross-sectional Analytics
 ranking · breadth · sectors · statistics
          │
          ├────────► Scanner Engine ───────► Alerts
          │
          ├────────► Strategy Lab ─────────► Backtester
          │
          ▼
      Order Request
          │
          ▼
       Risk Engine
          │
          ▼
      Order Manager
          │
     ┌────┴──────────┐
     ▼               ▼
Local Paper      IBKR Paper
     │               │
     └───────┬───────┘
             ▼
   SQLite Audit Journal
```

The Streamlit terminal is a thin presentation layer. Analytics, scanning, strategy, risk, portfolio, and execution logic live in framework packages under `src/rdqp`.

## Installation

Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .[dev,all]
pytest
streamlit run apps/terminal/streamlit_app.py
```

For Simulator-only operation:

```bash
pip install -e .[dev,ui]
streamlit run apps/terminal/streamlit_app.py
```

## IBKR paper setup

1. Log into a **paper** account in TWS or IB Gateway.
2. Enable API socket clients in IBKR API settings.
3. Use TWS paper port `7497` or Gateway paper port `4002`.
4. Keep market-data and execution client IDs distinct.
5. In the Execution page, type `PAPER`, arm routing, then connect.

The execution adapter rejects standard live ports. Live trading is not part of this release.

## Data persistence

- saved scanners: `data/saved_scans.yaml`
- saved strategies: `data/saved_strategies.yaml`
- execution orders and fills: `data/execution_journal.sqlite3`

## Tests

```text
32 passed
```

## Documentation

- `docs/architecture.md`
- `docs/scanner_engine.md`
- `docs/strategy_lab.md`
- `docs/execution_platform.md`
- `docs/roadmap.md`

## Important notice

This project is for research, education, and paper-trading validation. Yahoo Finance data may be delayed or incomplete. Confirm broker configuration and risk controls before submitting any paper order. No live-trading path is enabled in Sprint 5.
