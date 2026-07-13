"""Immutable strategy, trade, and backtest domain records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class RuleOperator(StrEnum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NE = "ne"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"


@dataclass(frozen=True, slots=True)
class StrategyRule:
    field: str
    operator: RuleOperator
    value: float | str | bool | None = None


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    name: str
    entry_rules: tuple[StrategyRule, ...]
    exit_rules: tuple[StrategyRule, ...] = ()
    initial_capital: float = 100_000.0
    allocation_pct: float = 0.10
    commission_per_trade: float = 0.0
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class TradeRecord:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    return_pct: float
    exit_reason: str


@dataclass(frozen=True, slots=True)
class EquityPoint:
    timestamp: datetime
    equity: float


@dataclass(frozen=True, slots=True)
class PerformanceMetrics:
    initial_capital: float
    final_equity: float
    total_return: float
    trade_count: int
    win_rate: float
    profit_factor: float | None
    max_drawdown: float
    expectancy: float
    sharpe_ratio: float | None


@dataclass(frozen=True, slots=True)
class BacktestResult:
    strategy_name: str
    trades: tuple[TradeRecord, ...]
    equity_curve: tuple[EquityPoint, ...]
    metrics: PerformanceMetrics
    warnings: tuple[str, ...] = field(default_factory=tuple)
