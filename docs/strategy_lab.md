# Strategy Lab

Sprint 4 adds a source-agnostic strategy research layer above the factor engine.

## Components

- `StrategyDefinition` and composable `StrategyRule` records
- `BacktestEngine` for long-only event-time simulations
- performance metrics: total return, win rate, profit factor, max drawdown, expectancy, and Sharpe proxy
- YAML persistence for saved visual strategies
- `PaperPortfolio` with positions, marking, realized/unrealized P&L, and journal entries
- Streamlit Strategy Lab with visual rule construction, backtest charts, trade list, and manual paper orders

## Boundaries

The Strategy Lab does not submit broker orders. Paper orders are entirely in memory and isolated from IBKR. Broker execution and production risk controls belong to Sprint 5.

The backtester uses the factor history currently loaded in the dashboard. Yahoo history is limited by the selected period and interval, while Simulator mode is deterministic and is recommended for local verification.
