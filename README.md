# RD Quant Platform

**Version:** `0.4.0-alpha`  
**Sprint:** 3 — Scanner Engine

RD Quant Platform is a modular, event-driven quantitative market analytics and trading framework inspired by the DolphinDB pattern of per-symbol stateful computation followed by cross-sectional analysis.

## Sprint 4 deliverables

Sprint 4 preserves the complete Sprint 2 dashboard and adds a configurable scanner subsystem as a separate application/domain package.

- All Sprint 1 architecture and Sprint 2 market-dashboard capabilities
- Configurable cross-sectional scanner engine
- Built-in scans:
  - Momentum Leaders
  - High RVOL
  - Gap Up
  - Gap Down
  - Opening Range Breakout
  - VWAP Reclaim
- Composable filter definitions
- Sorting, result direction, and result limits
- Custom scanner builder in Streamlit
- YAML-backed saved scans
- New-match alert engine
- Scanner alert feed
- Scanner latency and match-rate metrics
- Clickable scanner results linked to the shared selected-symbol panel
- Unit tests for filtering, alerts, and persistence

## Architecture

```text
Yahoo / IBKR / Simulator
          │
          ▼
   normalized Tick
          │
          ▼
 ReactiveFactorEngine
 ROC · RVOL · VWAP · Gap · ORB
          │
          ▼
 Cross-sectional analytics
 ranking · breadth · sectors · statistics
          │
          ├──────────────► ScannerEngine
          │                filters · sorting · limits
          │                         │
          │                         ├── AlertEngine
          │                         └── YAML Scan Repository
          ▼
 DashboardController
          │
          ▼
 Streamlit terminal
```

The scanner engine has no Streamlit, broker, or data-source dependency. It consumes normalized `FactorSnapshot` objects and returns immutable `ScanResult` values.

## Run

Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .[dev,all]
pytest
streamlit run apps/terminal/streamlit_app.py
```

For simulator-only use:

```bash
pip install -e .[dev,ui]
streamlit run apps/terminal/streamlit_app.py
```

## Scanner usage

1. Open the **Scanner** view.
2. Choose a built-in or saved scanner.
3. Review matches, match rate, and execution latency.
4. Click a result to make it the platform-wide selected symbol.
5. Build and save a custom scan using the form.
6. Enable new-match alerts to see symbols as they enter the active scan.

Custom scans are stored in `data/saved_scans.yaml`.

## Data-source notes

- **Simulator:** deterministic session data with enough history to calculate ROC immediately.
- **Yahoo Finance:** delayed, polled one-minute bars for learning and research.
- **IBKR:** read-only paper snapshots through TWS or IB Gateway. Data entitlements and line limits apply.

## Quality checks

```bash
pytest --cov=rdqp
ruff check src tests apps
black --check src tests apps
mypy src/rdqp
```

## Roadmap

- Sprint 1: architecture foundation — complete
- Sprint 2: streaming market dashboard — complete
- Sprint 4: configurable scanner engine, saved scans, and alerts — complete
- Sprint 4: strategy lab, backtesting, performance analytics, paper portfolio
- Sprint 5: IBKR paper execution, portfolio, risk, orders, and journal

Execution remains disabled by default.


## Sprint 4 — Strategy Lab

Sprint 4 is cumulative and retains the streaming dashboard and scanner engine. It adds:

- visual entry and exit rule builder
- saved YAML strategies
- event-time backtesting over loaded factor histories
- equity curve, trade list, total return, win rate, profit factor, drawdown, expectancy, and Sharpe proxy
- isolated in-memory paper portfolio
- manual paper orders, live marking, positions, P&L, and trade journal

Open **Strategy Lab** in the terminal after loading data. Simulator mode provides the deepest immediately available history. No Strategy Lab action sends an IBKR order.
