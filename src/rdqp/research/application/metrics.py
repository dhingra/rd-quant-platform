"""Research-grade metrics derived from a backtest result."""

from __future__ import annotations

import math
import statistics

from rdqp.research.domain.models import ExtendedMetrics
from rdqp.strategies.domain.models import BacktestResult


def extended_metrics(result: BacktestResult, periods_per_year: float = 252.0) -> ExtendedMetrics:
    curve = result.equity_curve
    returns: list[float] = []
    for previous, current in zip(curve, curve[1:], strict=False):
        if previous.equity > 0:
            returns.append(current.equity / previous.equity - 1.0)

    annualized_return = None
    annualized_volatility = None
    sortino = None
    if returns:
        average = statistics.fmean(returns)
        annualized_return = (1.0 + average) ** periods_per_year - 1.0 if average > -1 else -1.0
        if len(returns) > 1:
            deviation = statistics.stdev(returns)
            annualized_volatility = deviation * math.sqrt(periods_per_year)
            downside = [value for value in returns if value < 0]
            if len(downside) > 1:
                downside_deviation = statistics.stdev(downside)
                if downside_deviation > 0:
                    sortino = average / downside_deviation * math.sqrt(periods_per_year)

    metrics = result.metrics
    calmar = None
    if annualized_return is not None and metrics.max_drawdown < 0:
        calmar = annualized_return / abs(metrics.max_drawdown)
    recovery = None
    net_profit = metrics.final_equity - metrics.initial_capital
    if metrics.max_drawdown < 0:
        recovery = net_profit / (metrics.initial_capital * abs(metrics.max_drawdown))

    wins = [trade.pnl for trade in result.trades if trade.pnl > 0]
    losses = [abs(trade.pnl) for trade in result.trades if trade.pnl < 0]
    payoff = None
    if wins and losses:
        payoff = statistics.fmean(wins) / statistics.fmean(losses)

    holding = [
        (trade.exit_time - trade.entry_time).total_seconds() / 3600.0
        for trade in result.trades
    ]
    average_holding = statistics.fmean(holding) if holding else None
    return ExtendedMetrics(
        annualized_return,
        annualized_volatility,
        sortino,
        calmar,
        recovery,
        payoff,
        average_holding,
    )
