# Execution Platform

Sprint 5 adds a broker-neutral execution workflow:

`OrderRequest → RiskEngine → OrderManager → ExecutionBroker → SQLiteTradeJournal`

## Brokers

- **Local Paper** fills orders deterministically at the supplied reference, limit, or stop price.
- **IBKR Paper** connects only to standard paper ports (`7497` for TWS and `4002` for Gateway). The adapter rejects live ports and does not expose a live-trading mode.

## Risk controls

Every order is evaluated before it reaches a broker:

- maximum order notional
- maximum projected position notional
- daily loss limit
- maximum open orders
- maximum symbol quantity
- short-selling permission
- global kill switch
- buying-power validation

Risk rejections and broker errors are written to the same journal as accepted orders.

## Journal

`data/execution_journal.sqlite3` stores order state and fills. SQLite is used so the audit trail survives Streamlit reruns and process restarts without requiring a database server.

## Safety model

IBKR routing is disabled until the user types `PAPER`, arms the session, and connects explicitly. Standard live ports are blocked in code. This is a paper-execution milestone, not a live-trading release.
