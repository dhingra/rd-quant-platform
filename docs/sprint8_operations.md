# Sprint 8 — Scheduled Automation and Alert Operations

Sprint 8 adds an operator-controlled scheduling and alert layer around the guarded automation capability introduced in Sprint 7.

## Capabilities

- interval-based, single-process automation scheduler
- New York market-session guard with configurable timezone and session window
- weekend and paused-state protection
- automatic shutdown after repeated cycle failures
- deduplicated notifications with configurable cooldown
- in-memory terminal notification center
- append-only JSON Lines notification journal
- SQLite-backed persistent operator state
- Scheduler & Alerts terminal page

## Safety boundary

The scheduler is intentionally operator-driven and single-process. It does not create unattended broker sessions and does not automatically route orders to IBKR. Local paper automation remains the only schedulable execution path.

## Persistence

- scheduler/operator state: `data/automation_state.sqlite3`
- notifications: `data/notifications.jsonl`
- automation runs: `data/automation_runs.jsonl`
- automation paper orders: `data/automation_execution.sqlite3`
