# Roadmap

## Sprint 1 — Foundation (`0.1.0-alpha`)

- [x] repository and package structure
- [x] configuration and logging
- [x] immutable domain models
- [x] ports/interfaces
- [x] event bus
- [x] dependency injection
- [x] plugin registry
- [x] separate provider packages
- [x] simulator integration test
- [x] UI bootstrap and documentation

## Sprint 2 — Data and dashboard migration

- [ ] migrate the existing leaderboard UI into thin page/controller modules
- [ ] implement incremental ROC state engine
- [ ] implement cross-sectional ranking snapshots
- [ ] restore ROC histogram and descriptive statistics
- [ ] implement reliable row-to-symbol selection state
- [ ] migrate treemap, sector ranking, breadth, and time-series panels
- [ ] complete IBKR normalized tick subscription and reconnect handling
- [ ] harden Yahoo polling, stale-data markers, and session handling

## Sprint 3 — Scanner engine

- [ ] composable filter specification
- [ ] momentum, RVOL, gap, ORB, VWAP, and unusual-volume scanners
- [ ] saved scanner repository
- [ ] alerts and deduplication

## Sprint 4 — Strategy lab

- [ ] typed rule graph / visual rule builder
- [ ] historical replay and backtest engine
- [ ] performance analytics
- [ ] simulated portfolio and journal

## Sprint 5 — Execution platform

- [ ] IBKR paper order adapter
- [ ] order state machine
- [ ] pre-trade risk checks
- [ ] account/position synchronization
- [ ] kill switch and daily loss limits
- [ ] execution journal and reconciliation

## Release mapping

The product roadmap is cumulative: v4.0 includes all capabilities from v1.0 through v3.0. Development tags remain `0.x` until the first stable end-to-end release.
