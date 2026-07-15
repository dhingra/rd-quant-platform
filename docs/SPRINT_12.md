# Sprint 12 — Portfolio Intelligence & Risk Analytics

Sprint 12 adds a dependency-free portfolio intelligence package for long-only portfolio construction and institutional-style risk analysis.

## Capabilities

- Minimum-volatility, maximum-Sharpe, and target-return optimization
- Configurable minimum/maximum position weights
- Annualized return, volatility, and Sharpe estimates
- Covariance and correlation analysis
- Marginal, component, and percentage risk contribution
- Historical 95%/99% Value at Risk and 95% Expected Shortfall
- Portfolio beta against an optional benchmark
- Maximum drawdown from portfolio return history
- Deterministic market and symbol stress scenarios
- Current-to-target rebalance plans with turnover and transaction-cost estimates

The package is exposed through `rdqp.portfolio_intelligence` and remains independent of broker routing.
