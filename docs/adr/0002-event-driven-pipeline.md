# ADR 0002: Use an event-driven pipeline

## Status
Accepted

## Context
Stateful factors, rankings, scanners, strategies, execution, and portfolio accounting evolve at different rates.

## Decision
Publish normalized domain events and let independent handlers subscribe to them.

## Consequences
Components remain loosely coupled. Event ordering, observability, error handling, and eventual durable transport require deliberate design.
