# Scanner Engine

Sprint 3 introduces a scanner subsystem that consumes the latest `FactorSnapshot` cross section and produces deterministic `ScanResult` objects.

## Design

- `ScannerEngine` is pure application logic and has no Streamlit, Yahoo, or IBKR dependency.
- `ScanDefinition` contains composable filters, sorting, direction, and a result limit.
- `YamlScanRepository` persists user-defined scans without coupling the engine to storage.
- `AlertEngine` emits alerts only when a symbol newly enters a scan.
- The dashboard controller is the application boundary used by the terminal UI.

## Supported fields

`roc_pct`, `rvol`, `gap_pct`, `vwap_distance_pct`, `price`, `volume`, `rank`, `sector`, `above_vwap`, `orb_breakout`, and `orb_breakdown`.

## Supported operators

`>`, `>=`, `<`, `<=`, `==`, `!=`, `in`, `not_in`, `between`, `contains`, `is_true`, and `is_false`.

## Built-in scans

- Momentum Leaders
- High RVOL
- Gap Up
- Gap Down
- ORB Breakout
- VWAP Reclaim

Saved scans are stored in `data/saved_scans.yaml` and are intentionally excluded from core domain logic.
