# Changelog

## 0.11.0a1 — Sprint 11

- Added research-workstation performance series.
- Added trade explorer analytics and filters.
- Added portfolio allocation and sector exposure analytics.
- Added deterministic replay playback controller.
- Added workstation tests and documentation.


## 0.9.0-alpha — Sprint 9

- Added Research & Optimization Lab.
- Added deterministic grid-search parameter optimization.
- Added rolling walk-forward validation.
- Added seeded Monte Carlo trade-sequence analysis.
- Added extended performance metrics.
- Added SQLite experiment tracking and Research Lab UI.
- Added research tests and documentation.

## 0.7.0-alpha — Sprint 8

### Added
- operator-controlled automation scheduler
- configurable market-session and weekend guards
- scheduler pause/resume and repeated-failure shutdown
- notification router with cooldown deduplication
- in-memory and JSONL notification sinks
- persistent SQLite automation state store
- Scheduler & Alerts terminal page
- Sprint 8 documentation and tests

## 0.5.0-alpha — Sprint 5

- Added broker-neutral execution models and ports.
- Added local paper execution broker.
- Added explicitly armed IBKR paper broker with live-port rejection.
- Added pre-trade risk engine, order manager, account synchronization, order management, and SQLite audit journal.
- Added Execution page with positions, account metrics, risk controls, ticket, orders, and fills.
- Added execution and risk unit tests.

# Changelog

## 0.4.0-alpha — Sprint 4

### Added

- visual strategy builder with composable entry and exit rules
- YAML-backed saved strategy repository
- source-agnostic event-time backtesting engine
- equity curve and trade-level results
- total return, win rate, profit factor, max drawdown, expectancy, and Sharpe proxy
- in-memory paper portfolio with buy/sell fills
- live marking, realized and unrealized P&L
- paper trade journal
- Strategy Lab tests and documentation

### Retained

All Sprint 1–3 architecture, dashboard, market analytics, data providers, scanners, saved scans, and alerts.

## 0.6.0-alpha — Sprint 6

### Added
- normalized CSV market-session recorder
- deterministic event-time replay engine with batching and optional pacing
- Replay & Ops terminal page
- component health checks and runtime metrics registry
- replay and observability unit tests
- operational architecture documentation

## 0.6.0-alpha — Sprint 7

### Added
- guarded saved-strategy automation runner
- DISABLED, DRY_RUN, and PAPER_ARMED modes
- per-cycle order cap, open-position cap, symbol cooldown, and positive-ROC guard
- local paper execution integration through the existing risk engine and order manager
- JSON Lines automation audit journal and separate execution journal
- Automation page in the Streamlit terminal
- automation unit tests and documentation

### Safety
- automated IBKR routing is not enabled
- live trading remains unsupported

## 0.10.0-alpha — Sprint 10

- Added weighted multi-factor ranking.
- Added deployment-readiness scorecards.
- Added strategy comparison and robustness analysis.
- Added optimization heatmaps and walk-forward charts.
- Corrected Monte Carlo sampling to bootstrap with replacement.
