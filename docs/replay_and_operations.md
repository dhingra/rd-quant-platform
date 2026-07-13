# Replay and Operations

Sprint 6 adds deterministic historical replay and lightweight operational visibility.

## Session recording

The terminal converts current normalized factor history back into normalized `Tick` records and stores them in `data/market_session.csv`. The CSV adapter is intentionally broker-neutral and can be used by tests, scanners, and strategy research.

## Replay

`ReplayEngine` sorts all input by event timestamp and symbol, then sends bounded batches to a caller-supplied handler. It does not import Streamlit, analytics, or execution code. A speed multiplier can emulate event-time pacing; zero means maximum speed.

## Observability

`HealthMonitor` isolates infrastructure checks so one failed dependency cannot hide the status of other components. `MetricsRegistry` provides simple counters and gauges for an in-process terminal. A future deployment can adapt these ports to Prometheus or OpenTelemetry.

## Safety

Replay never routes broker orders. Execution remains separately armed and risk-gated.
