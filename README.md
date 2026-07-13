# RD Quant Platform

**Version:** `0.1.0-alpha`  
**Sprint:** Foundation / architecture refactor

RD Quant Platform is a modular, event-driven quantitative research and execution framework. It is inspired by the streaming pattern used in DolphinDB—stateful per-symbol calculations followed by cross-sectional market analysis—and extends that pattern toward scanners, strategies, portfolio management, and guarded broker execution.

This release is the architectural foundation. It intentionally prioritizes clean boundaries, replaceable adapters, and tests before migrating the full dashboard.

## What is implemented in Sprint 1

- `src/` package layout with bounded contexts
- immutable domain models for ticks, bars, quotes, signals, orders, trades, positions, and portfolios
- market-data and execution ports (interfaces)
- asynchronous in-process event bus with handler isolation
- dependency-injection composition root
- typed YAML configuration with environment overrides
- centralized logging configuration
- plugin registry
- separate provider packages:
  - `datasources.simulator` — functional streaming provider
  - `datasources.yahoo` — functional polling adapter when the Yahoo extra is installed
  - `datasources.ibkr` — connection lifecycle and package boundary; tick subscription migration follows in Sprint 2
- thin Streamlit bootstrap with no trading logic
- unit and integration tests
- CI, linting, formatting, typing, and pre-commit configuration
- architecture documentation and ADRs

## Planned cumulative platform

### v1.0 — Streaming Dashboard

Stable data layer, reactive factor engine, cross-sectional analytics, ROC distribution, treemap, sector ranking, market breadth, clickable symbols, and live charts.

### v2.0 — Scanner Engine

Configurable filters, saved scans, alerts, momentum, gap, RVOL, opening-range, VWAP, and unusual-volume scanners.

### v3.0 — Strategy Lab

Visual strategy rules, backtesting, performance analytics, position sizing, and paper portfolio.

### v4.0 — Execution Platform

Everything in v1.0–v3.0 plus IBKR paper execution, portfolio management, risk controls, order management, and trade journal.

## Architecture

```text
Market data adapters (Yahoo / IBKR / Simulator)
                         │
                         ▼
               Normalized Tick / Bar
                         │
                         ▼
                    Event Bus
                         │
         ┌───────────────┼────────────────┐
         ▼               ▼                ▼
  Factor engine   Cross-sectional     Persistence
                         │
                         ▼
                 Scanner / Strategy
                         │
                         ▼
                  Risk / Execution
                         │
                         ▼
                 Portfolio / Journal
```

The framework depends on ports such as `MarketDataProvider` and `Broker`. Yahoo, IBKR, and Simulator are adapters. The Streamlit terminal is another adapter and does not own trading logic.

## Quick start

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -e .[dev,ui]
pytest
rdqp --ticks 20
streamlit run apps/terminal/streamlit_app.py
```

For Yahoo support:

```bash
pip install -e .[yahoo,ui]
```

For IBKR support:

```bash
pip install -e .[ibkr,ui]
```

## Configuration

Edit `config/app.yaml`. Environment variables can override any nested setting:

```bash
export RDQP__MARKET_DATA__PROVIDER=yahoo
export RDQP__APP__LOG_LEVEL=DEBUG
```

Double underscores delimit nested keys.

## IBKR safety

Execution is disabled by default. The current IBKR adapter connects read-only and uses the paper-trading port in configuration. Live execution will remain behind explicit configuration, account checks, confirmation, and risk controls.

## Tests and quality checks

```bash
pytest --cov=rdqp
ruff check src tests apps
black --check src tests apps
mypy src/rdqp
pre-commit run --all-files
```

## Repository map

```text
apps/terminal/          Thin Streamlit application
config/                 Runtime configuration
docs/                   Architecture, roadmap, ADRs
src/rdqp/platform/      Config, logging, event bus, DI, plugins
src/rdqp/market/        Market domain, ports, application services
src/rdqp/datasources/   Yahoo, IBKR, Simulator adapters
src/rdqp/analytics/     Factor and cross-sectional domains
src/rdqp/scanners/      Scanner context
src/rdqp/strategies/    Strategy context
src/rdqp/portfolio/     Portfolio context
src/rdqp/execution/     Broker and execution context
tests/                  Unit and integration tests
```

## Current limitations

- Sprint 1 is a foundation release, not the completed v4.0 terminal.
- The previous dashboard has not yet been migrated into this repository.
- Yahoo is polled and is not execution-grade market data.
- The IBKR adapter's connection lifecycle is present; normalized tick streaming is scheduled for Sprint 2.
- The event bus is in-process. A durable broker can be introduced behind the same abstraction later.

See [`docs/roadmap.md`](docs/roadmap.md) for the implementation sequence.
