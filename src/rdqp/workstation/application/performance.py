"""Derived performance series for interactive workstation charts."""

from __future__ import annotations

import math
import statistics
from collections import deque
from datetime import datetime

from rdqp.strategies.domain.models import BacktestResult
from rdqp.workstation.domain.models import MonthlyReturn, PerformanceSeries, TimeSeriesPoint


def build_performance_series(
    result: BacktestResult,
    rolling_window: int = 20,
    annualization_periods: int = 252,
) -> PerformanceSeries:
    """Build equity, drawdown, rolling risk, and monthly-return series."""
    if rolling_window < 2:
        raise ValueError("rolling_window must be at least 2")
    if annualization_periods < 1:
        raise ValueError("annualization_periods must be positive")

    equity = tuple(TimeSeriesPoint(point.timestamp, point.equity) for point in result.equity_curve)
    drawdown: list[TimeSeriesPoint] = []
    rolling_sharpe: list[TimeSeriesPoint] = []
    rolling_volatility: list[TimeSeriesPoint] = []
    returns_window: deque[float] = deque(maxlen=rolling_window)
    peak = result.metrics.initial_capital
    previous = result.metrics.initial_capital

    for point in result.equity_curve:
        peak = max(peak, point.equity)
        value = point.equity / peak - 1 if peak else 0.0
        drawdown.append(TimeSeriesPoint(point.timestamp, value))

        period_return = point.equity / previous - 1 if previous > 0 else 0.0
        previous = point.equity
        returns_window.append(period_return)
        if len(returns_window) < 2:
            rolling_sharpe.append(TimeSeriesPoint(point.timestamp, 0.0))
            rolling_volatility.append(TimeSeriesPoint(point.timestamp, 0.0))
            continue

        volatility = statistics.stdev(returns_window) * math.sqrt(annualization_periods)
        mean_return = statistics.fmean(returns_window)
        sharpe = (
            mean_return / statistics.stdev(returns_window) * math.sqrt(annualization_periods)
            if statistics.stdev(returns_window) > 0
            else 0.0
        )
        rolling_sharpe.append(TimeSeriesPoint(point.timestamp, sharpe))
        rolling_volatility.append(TimeSeriesPoint(point.timestamp, volatility))

    return PerformanceSeries(
        equity=equity,
        drawdown=tuple(drawdown),
        rolling_sharpe=tuple(rolling_sharpe),
        rolling_volatility=tuple(rolling_volatility),
        monthly_returns=_monthly_returns(result),
    )


def _monthly_returns(result: BacktestResult) -> tuple[MonthlyReturn, ...]:
    closes: dict[tuple[int, int], tuple[datetime, float]] = {}
    opens: dict[tuple[int, int], tuple[datetime, float]] = {}
    for point in result.equity_curve:
        key = (point.timestamp.year, point.timestamp.month)
        if key not in opens or point.timestamp < opens[key][0]:
            opens[key] = (point.timestamp, point.equity)
        if key not in closes or point.timestamp > closes[key][0]:
            closes[key] = (point.timestamp, point.equity)

    rows: list[MonthlyReturn] = []
    for year, month in sorted(opens):
        start = opens[(year, month)][1]
        end = closes[(year, month)][1]
        rows.append(MonthlyReturn(year, month, end / start - 1 if start else 0.0))
    return tuple(rows)
