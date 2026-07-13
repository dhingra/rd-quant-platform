# Research & Optimization Lab

Sprint 9 adds reproducible research workflows without coupling them to Streamlit or broker execution.

## Components

- `GridSearchOptimizer`: deterministic Cartesian parameter search over supported strategy risk fields.
- `WalkForwardEngine`: rolling train/test validation using event-time factor histories.
- `MonteCarloEngine`: seeded trade-sequence reshuffling and final-equity confidence ranges.
- `extended_metrics`: Sortino, Calmar, recovery factor, payoff ratio, annualized estimates, and holding time.
- `SqliteExperimentRepository`: durable experiment metadata, strategy definitions, parameters, metrics, and notes.

## Safety and interpretation

Research outputs are estimates, not guarantees. Optimization can overfit small samples. Walk-forward results should be preferred over in-sample rankings, and Monte Carlo reshuffling does not model regime changes, liquidity constraints, or correlated simultaneous positions.

Research code never routes orders. Promotion of a strategy into automation remains an explicit operator action through the existing guarded workflow.
