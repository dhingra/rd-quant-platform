"""Domain records for the Sprint 11 research workstation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TimeSeriesPoint:
    timestamp: datetime
    value: float


@dataclass(frozen=True, slots=True)
class MonthlyReturn:
    year: int
    month: int
    return_pct: float


@dataclass(frozen=True, slots=True)
class PerformanceSeries:
    equity: tuple[TimeSeriesPoint, ...]
    drawdown: tuple[TimeSeriesPoint, ...]
    rolling_sharpe: tuple[TimeSeriesPoint, ...]
    rolling_volatility: tuple[TimeSeriesPoint, ...]
    monthly_returns: tuple[MonthlyReturn, ...]


@dataclass(frozen=True, slots=True)
class TradeSummary:
    trade_count: int
    winners: int
    losers: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    net_pnl: float
    average_pnl: float
    median_pnl: float
    average_holding_hours: float
    best_trade: float
    worst_trade: float


@dataclass(frozen=True, slots=True)
class PortfolioSlice:
    label: str
    value: float
    weight: float


@dataclass(frozen=True, slots=True)
class PortfolioAnalytics:
    equity: float
    cash: float
    invested: float
    realized_pnl: float
    unrealized_pnl: float
    allocations: tuple[PortfolioSlice, ...]
    sector_exposure: tuple[PortfolioSlice, ...]


@dataclass(frozen=True, slots=True)
class ReplayState:
    cursor: int
    total: int
    speed: float
    playing: bool

    @property
    def progress(self) -> float:
        return self.cursor / self.total if self.total else 0.0
