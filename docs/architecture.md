# Architecture

RD Quant Platform uses ports-and-adapters architecture with bounded contexts.

## Dependency rule

Domain and application code do not import Streamlit, Yahoo Finance, or IBKR. Infrastructure adapters depend inward on market and execution ports. The composition root in `rdqp.app` chooses concrete implementations from configuration.

## Contexts

- **platform:** configuration, logging, event bus, DI, plugin registry
- **market:** normalized market models, provider port, stream use cases
- **datasources:** Yahoo, IBKR, and Simulator adapters
- **analytics:** indicators and cross-sectional calculations
- **scanners:** configurable market screening
- **strategies:** signal generation and backtesting rules
- **portfolio:** positions, cash, P&L, and accounting
- **execution:** broker port, orders, risk, and journal
- **dashboard:** presentation components only

## Streaming flow

1. A provider emits a normalized `Tick` or `Bar`.
2. `MarketStreamService` publishes an event.
3. Factor subscribers maintain symbol-local state.
4. Cross-sectional subscribers rank the latest factor snapshot.
5. Scanners and strategies consume analytics events.
6. Execution consumes approved order requests.
7. Portfolio and journal consume fills.

## SOLID application

- **Single responsibility:** connection, market data, analytics, execution, and UI are separate.
- **Open/closed:** new providers implement `MarketDataProvider` without modifying analytics.
- **Liskov substitution:** all adapters produce the same normalized models.
- **Interface segregation:** market data and order execution use separate ports.
- **Dependency inversion:** application services depend on abstractions, not Yahoo or IBKR.
