"""Factor quintile and decile forward-return analysis."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from statistics import fmean, median

from rdqp.factor_lab.application.correlation import pearson_correlation
from rdqp.factor_lab.domain.information import (
    ForwardReturnObservation,
    QuantileAnalysis,
    QuantileBucket,
)
from rdqp.factor_lab.domain.models import FactorCrossSection


class QuantileReturnAnalyzer:
    """Split factor scores into equal-count buckets and summarize returns."""

    def analyze(
        self,
        cross_section: FactorCrossSection,
        forward_returns: Mapping[str, float] | Iterable[ForwardReturnObservation],
        buckets: int = 5,
        horizon: int = 1,
    ) -> QuantileAnalysis:
        if buckets < 2:
            raise ValueError("at least two buckets are required")
        if horizon <= 0:
            raise ValueError("horizon must be positive")

        if isinstance(forward_returns, Mapping):
            returns = {symbol.upper(): value for symbol, value in forward_returns.items()}
        else:
            returns = {
                row.symbol: row.return_value
                for row in forward_returns
                if row.timestamp == cross_section.timestamp and row.horizon == horizon
            }

        matched = sorted(
            (
                (score.score, score.symbol, returns[score.symbol])
                for score in cross_section.scores
                if score.symbol in returns
            ),
            key=lambda item: (item[0], item[1]),
        )
        bucket_returns: list[list[float]] = [[] for _ in range(buckets)]
        for index, (_, _, realized_return) in enumerate(matched):
            bucket = min(index * buckets // max(len(matched), 1), buckets - 1)
            bucket_returns[bucket].append(realized_return)

        summaries = tuple(
            QuantileBucket(
                bucket=index + 1,
                label=f"Q{index + 1}" if buckets == 5 else f"D{index + 1}",
                observations=len(values),
                mean_return=fmean(values) if values else None,
                median_return=median(values) if values else None,
            )
            for index, values in enumerate(bucket_returns)
        )
        bottom = summaries[0].mean_return
        top = summaries[-1].mean_return
        spread = None if bottom is None or top is None else top - bottom
        populated = [bucket for bucket in summaries if bucket.mean_return is not None]
        monotonicity = pearson_correlation(
            [float(bucket.bucket) for bucket in populated],
            [bucket.mean_return for bucket in populated if bucket.mean_return is not None],
        )
        return QuantileAnalysis(
            factor=cross_section.factor.name,
            timestamp=cross_section.timestamp,
            horizon=horizon,
            bucket_count=buckets,
            buckets=summaries,
            long_short_spread=spread,
            monotonicity=monotonicity,
        )
