# Factor Lab Core

Sprint 13.1 introduces a dependency-free cross-sectional research layer under
`rdqp.factor_lab`.

## Workflow

1. Define a factor with `FactorDefinition`.
2. Convert analytics snapshots or research data into `FactorObservation` records.
3. Normalize one timestamp's cross-section with `FactorNormalizer`.
4. Analyze pairwise relationships with `FactorCorrelationAnalyzer`.

The core supports winsorization, population z-scores, tie-aware percentile ranks,
missing values, inverse factor direction, and pairwise-complete correlations.
Information coefficients, quantile portfolios, factor decay, and regimes are reserved
for later Sprint 13 increments.
