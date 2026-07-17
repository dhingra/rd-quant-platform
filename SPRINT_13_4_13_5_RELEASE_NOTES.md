# Sprint 13.4–13.5 Release Notes

## Strategy Selection

- Regime-tagged strategy performance records
- Configurable eligibility gates for trade count, drawdown, and current-regime return
- Weighted strategy score using return, Sharpe, drawdown quality, and profit factor
- Confidence-aware scoring from the current regime classification
- Ranked recommendations with explicit rejection reasons
- Normalized top-N ensemble allocations

## Streamlit Integration

- New Factor & Regime Lab page
- CSV-backed factor leaderboard
- Raw, z-score, and percentile normalization
- Higher-is-better and inverse-factor handling
- Interactive market-regime controls
- Current trend, volatility, breadth, risk regime, and confidence metrics
- Saved strategy discovery
- Editable strategy-by-regime performance table
- Recommendation and ensemble-allocation views

## Safety

The selection engine only generates research recommendations. It does not route orders or bypass paper-trading and risk controls.
