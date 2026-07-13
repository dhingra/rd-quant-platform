# RD Quant Platform

**Version:** `0.2.0-alpha`  
**Sprint:** 2 — Streaming Dashboard

RD Quant Platform is a modular, event-driven quantitative market analytics and trading framework inspired by the DolphinDB pattern of per-symbol stateful computation followed by cross-sectional analysis.

## Sprint 2 deliverables

Sprint 2 builds on the SOLID foundation from Sprint 1 and adds a runnable market dashboard without moving business logic into Streamlit.

- Live multi-source dashboard adapters:
  - Simulator with immediate event-time history
  - Yahoo Finance recent 1-minute bars
  - IBKR TWS / Gateway read-only paper snapshots
- Incremental `ReactiveFactorEngine`
  - event-time ROC
  - RVOL
  - VWAP and VWAP distance
  - gap analysis
  - opening-range state
- Cross-sectional ranking
- Market statistics:
  - mean ROC
  - median ROC
  - standard deviation
  - skew
  - percentage positive
- Market breadth
- ROC histogram
- momentum breadth gauge
- sector ranking
- Finviz-style treemap
- clickable leader and laggard rows
- selected-symbol price, VWAP, ROC, and volume charts
- controller layer that keeps analytics out of the UI
- unit and integration tests

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
          ▼
 DashboardController
          │
          ▼
 Streamlit terminal
```

The Streamlit layer renders data and handles user interaction. It does not calculate factors or rankings.

## Run

Python 3.11 or newer:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .[dev,all]
pytest
streamlit run apps/terminal/streamlit_app.py
```

For the smallest simulator-only installation:

```bash
pip install -e .[dev,ui]
streamlit run apps/terminal/streamlit_app.py
```

## Data-source notes

### Simulator

Starts with enough synthetic event-time history to calculate ROC immediately. It is deterministic within a dashboard session and is intended for development and demonstrations.

### Yahoo Finance

Yahoo supplies delayed, polled one-minute bars. It is suitable for learning, research, and dashboard prototyping, but not for execution-grade decisions.

### IBKR

The Sprint 2 terminal requests read-only market-data snapshots from TWS or IB Gateway. Defaults are configured for the TWS paper port (`7497`) and delayed data type (`3`). Market-data subscriptions and IBKR line limits still apply.

## Row selection

Leader and laggard tables use Streamlit's single-row selection event. The selected table row updates one shared `selected_symbol`, which drives every detail card and chart. This fixes the earlier mismatch between a clicked row and the displayed ticker.

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
- Sprint 3: configurable scanner engine, saved scans, and alerts
- Sprint 4: strategy lab, backtesting, performance analytics, paper portfolio
- Sprint 5: IBKR paper execution, portfolio, risk, orders, and journal

Execution remains disabled by default.
