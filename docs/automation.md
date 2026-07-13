# Sprint 7 — Guarded Strategy Automation

Sprint 7 connects saved Strategy Lab definitions to the existing risk and execution layers without enabling live trading.

## Pipeline

```text
Factor snapshots → saved strategy rules → automation guards → risk engine → order manager → local paper broker → audit journals
```

## Modes

- `DISABLED`: evaluates nothing and records the disabled state.
- `DRY_RUN`: produces proposed actions without submitting orders.
- `PAPER_ARMED`: submits risk-checked orders to the local paper broker after explicit UI confirmation.

## Safety controls

- maximum orders per cycle
- maximum open positions
- per-symbol cooldown
- positive-ROC entry guard
- existing centralized risk limits and kill switch
- append-only automation run journal
- separate SQLite execution journal

IBKR automation and live-account automation are intentionally unavailable in Sprint 7. IBKR remains manual and paper-only through the Execution page.
