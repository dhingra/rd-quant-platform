# Sprint 13.1 — Factor Lab Core

This increment establishes the typed, dependency-free foundation for cross-sectional factor research.

## Included

- Immutable factor metadata and observation models
- Winsorization with interpolated quantiles
- Population z-score normalization
- Tie-aware percentile ranking
- Direction-aware factor scores
- Missing-value handling
- Pairwise-complete Pearson correlations
- Adapter from `FactorSnapshot` to factor observations
- Factor Lab architecture documentation
- Unit tests for normalization, correlation, and snapshot mapping

## Deferred to later Sprint 13 increments

- Information coefficient and rank IC
- Quantile portfolio returns
- Factor decay
- Turnover and capacity analysis
- Market-regime classification
- Regime-aware strategy selection
- Streamlit Factor & Regime Lab page

## Validation

- Python compilation: passed
- Pytest: 72 passed
- Ruff/mypy: run locally or in GitHub Actions; those tools were not installed in the packaging runtime
