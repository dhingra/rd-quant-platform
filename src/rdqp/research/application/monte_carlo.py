"""Monte Carlo analysis based on shuffled realized trade returns."""

from __future__ import annotations

import random
import statistics

from rdqp.research.domain.models import MonteCarloSummary
from rdqp.strategies.domain.models import BacktestResult


class MonteCarloEngine:
    def run(self, result: BacktestResult, simulations: int = 1_000, seed: int = 7) -> MonteCarloSummary:
        if simulations <= 0:
            raise ValueError("simulations must be positive")
        returns = [trade.return_pct for trade in result.trades]
        initial = result.metrics.initial_capital
        rng = random.Random(seed)
        finals: list[float] = []
        drawdowns: list[float] = []
        for _ in range(simulations):
            sample = returns.copy()
            rng.shuffle(sample)
            equity = initial
            peak = initial
            max_drawdown = 0.0
            for trade_return in sample:
                equity *= 1.0 + trade_return
                peak = max(peak, equity)
                max_drawdown = min(max_drawdown, equity / peak - 1.0)
            finals.append(equity)
            drawdowns.append(max_drawdown)
        finals.sort()
        drawdowns.sort()
        return MonteCarloSummary(
            simulations=simulations,
            median_final_equity=statistics.median(finals),
            percentile_5_final_equity=self._percentile(finals, 0.05),
            percentile_95_final_equity=self._percentile(finals, 0.95),
            probability_of_loss=sum(value < initial for value in finals) / simulations,
            median_max_drawdown=statistics.median(drawdowns),
            final_equities=tuple(finals),
        )

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        if not values:
            return 0.0
        index = min(len(values) - 1, max(0, round((len(values) - 1) * percentile)))
        return values[index]
