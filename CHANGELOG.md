# Changelog

## 0.3.0-alpha — Sprint 3

- Added configurable, composable cross-sectional scanner engine.
- Added Momentum, High RVOL, Gap Up, Gap Down, ORB, and VWAP Reclaim presets.
- Added YAML-backed saved scanner definitions.
- Added custom scanner builder and scanner result row selection.
- Added new-match alert engine and terminal alert feed.
- Added scan latency, universe size, and match-rate metrics.
- Added scanner domain, application, and infrastructure tests.
- Preserved all Sprint 1 and Sprint 2 functionality.

## 0.2.0-alpha — Sprint 2

- Added reactive factor engine and event-time ROC.
- Added RVOL, VWAP distance, gap, and opening-range analytics.
- Added cross-sectional ranking, statistics, breadth, and sector strength.
- Added dashboard controller and full Streamlit market terminal.
- Added ROC histogram, breadth gauge, treemap, sector ranking, and symbol charts.
- Added Yahoo recent-bar and IBKR read-only snapshot adapters.
- Fixed selected-row-to-symbol synchronization.
- Added analytics and dashboard integration tests.


## 0.1.0-alpha.1

### Added
- SOLID package boundaries and ports/adapters layout
- typed domain models
- asynchronous event bus
- dependency-injection container
- YAML configuration with environment overrides
- plugin registry
- Simulator, Yahoo, and IBKR provider packages
- CLI and Streamlit bootstrap
- unit/integration tests and CI
- architecture documentation and ADRs
