# Sprint 14.1 — IBKR Account Synchronization

Sprint 14.1 introduces a read-oriented, paper-account-only synchronization boundary for Interactive Brokers.

## Capabilities

- account summary synchronization
- cash, buying power, net liquidation, and realized/unrealized P&L
- position synchronization with market-price fallback
- open-order synchronization
- execution/fill synchronization
- disconnected, stale, and error health states
- injectable reader protocol for deterministic tests
- paper-port enforcement (`7497` and `4002`)
- readonly connection support by default

## Safety boundary

The synchronization adapter refuses live ports and does not submit, replace, or cancel orders. Order lifecycle changes remain in later Sprint 14 increments.
