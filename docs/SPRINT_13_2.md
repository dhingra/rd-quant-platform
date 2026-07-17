# Sprint 13.2 — Information Coefficient

Sprint 13.2 extends Factor Lab Core with predictive-power diagnostics.

## Capabilities

- Pearson Information Coefficient between normalized factor scores and forward returns.
- Spearman Rank IC with average-rank tie handling.
- Time-series IC summaries including mean IC, information ratio, and hit rate.
- Equal-count quintile and decile return analysis.
- Top-minus-bottom long-short factor spreads and monotonicity diagnostics.
- IC decay profiles across multiple forward-return horizons.
- A report builder combining IC series, quantile analyses, and decay outputs.

Forward returns are explicitly aligned to the factor formation timestamp and a positive integer horizon. This keeps research inputs deterministic and avoids hidden look-ahead assumptions.
