# Sprint 13.3 — Regime Engine

Sprint 13.3 adds a deterministic market-regime engine to the Factor Lab.

## Capabilities

- Trend classification: bull, neutral, bear
- Volatility classification: low, normal, high
- Breadth classification: strong, mixed, weak
- Composite risk-on, neutral, and risk-off regimes
- Configurable thresholds
- Confidence scores
- Chronological regime history
- Composite regime-transition detection

The engine is side-effect free and receives explicit observations, which keeps research and replay results reproducible.
