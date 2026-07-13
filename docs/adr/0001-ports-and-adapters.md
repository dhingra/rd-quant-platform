# ADR 0001: Use ports and adapters

## Status
Accepted

## Context
Market data may come from Yahoo, IBKR, simulation, or replay. UI and execution technology will also evolve.

## Decision
Domain and application services depend on narrow ports. External technologies live in adapter packages and are selected in a composition root.

## Consequences
Adapters are replaceable and testable, but explicit mapping and dependency wiring are required.
