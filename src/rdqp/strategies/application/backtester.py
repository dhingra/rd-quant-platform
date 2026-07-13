"""Long-only event-time backtester for factor snapshots."""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.strategies.application.evaluator import evaluate_all
from rdqp.strategies.domain.models import (
    BacktestResult,
    EquityPoint,
    PerformanceMetrics,
    StrategyDefinition,
    TradeRecord,
)


class BacktestEngine:
    """Backtest strategies without depending on Streamlit or a broker adapter."""

    def run(
        self,
        definition: StrategyDefinition,
        histories: Mapping[str, Sequence[FactorSnapshot]],
    ) -> BacktestResult:
        cash = definition.initial_capital
        trades: list[TradeRecord] = []
        equity_points: list[EquityPoint] = []
        warnings: list[str] = []

        events = sorted(
            (snapshot.timestamp, symbol, snapshot)
            for symbol, history in histories.items()
            for snapshot in history
        )
        positions: dict[str, tuple[FactorSnapshot, int]] = {}
        latest_prices: dict[str, float] = {}

        if not events:
            warnings.append("No factor history is available. Refresh market data first.")

        for timestamp, symbol, snapshot in events:
            latest_prices[symbol] = snapshot.price
            position = positions.get(symbol)
            if position is None and evaluate_all(snapshot, definition.entry_rules):
                budget = min(cash, definition.initial_capital * definition.allocation_pct)
                quantity = int(budget // snapshot.price)
                if quantity > 0:
                    cash -= quantity * snapshot.price + definition.commission_per_trade
                    positions[symbol] = (snapshot, quantity)
            elif position is not None:
                entry, quantity = position
                price_return = snapshot.price / entry.price - 1
                reason: str | None = None
                if (
                    definition.stop_loss_pct is not None
                    and price_return <= -definition.stop_loss_pct
                ):
                    reason = "stop_loss"
                elif (
                    definition.take_profit_pct is not None
                    and price_return >= definition.take_profit_pct
                ):
                    reason = "take_profit"
                elif definition.exit_rules and evaluate_all(snapshot, definition.exit_rules):
                    reason = "exit_rules"
                if reason:
                    proceeds = quantity * snapshot.price - definition.commission_per_trade
                    cash += proceeds
                    pnl = (
                        snapshot.price - entry.price
                    ) * quantity - 2 * definition.commission_per_trade
                    trades.append(
                        TradeRecord(
                            symbol=symbol,
                            entry_time=entry.timestamp,
                            exit_time=snapshot.timestamp,
                            entry_price=entry.price,
                            exit_price=snapshot.price,
                            quantity=quantity,
                            pnl=pnl,
                            return_pct=price_return,
                            exit_reason=reason,
                        )
                    )
                    del positions[symbol]

            market_value = sum(
                qty * latest_prices.get(sym, entry.price) for sym, (entry, qty) in positions.items()
            )
            equity_points.append(EquityPoint(timestamp, cash + market_value))

        if events:
            final_time = events[-1][0]
            for symbol, (entry, quantity) in list(positions.items()):
                exit_price = latest_prices.get(symbol, entry.price)
                cash += quantity * exit_price - definition.commission_per_trade
                pnl = (exit_price - entry.price) * quantity - 2 * definition.commission_per_trade
                trades.append(
                    TradeRecord(
                        symbol=symbol,
                        entry_time=entry.timestamp,
                        exit_time=final_time,
                        entry_price=entry.price,
                        exit_price=exit_price,
                        quantity=quantity,
                        pnl=pnl,
                        return_pct=exit_price / entry.price - 1,
                        exit_reason="end_of_data",
                    )
                )
            equity_points.append(EquityPoint(final_time, cash))

        metrics = self._metrics(definition.initial_capital, cash, trades, equity_points)
        return BacktestResult(
            definition.name, tuple(trades), tuple(equity_points), metrics, tuple(warnings)
        )

    @staticmethod
    def _metrics(
        initial_capital: float,
        final_equity: float,
        trades: list[TradeRecord],
        curve: list[EquityPoint],
    ) -> PerformanceMetrics:
        wins = [trade.pnl for trade in trades if trade.pnl > 0]
        losses = [trade.pnl for trade in trades if trade.pnl < 0]
        win_rate = len(wins) / len(trades) if trades else 0.0
        profit_factor = sum(wins) / abs(sum(losses)) if losses else (math.inf if wins else None)
        expectancy = statistics.fmean([trade.pnl for trade in trades]) if trades else 0.0
        peak = initial_capital
        max_drawdown = 0.0
        returns: list[float] = []
        previous = initial_capital
        for point in curve:
            peak = max(peak, point.equity)
            if peak:
                max_drawdown = min(max_drawdown, point.equity / peak - 1)
            if previous > 0 and point.equity != previous:
                returns.append(point.equity / previous - 1)
            previous = point.equity
        sharpe = None
        if len(returns) >= 2:
            deviation = statistics.stdev(returns)
            if deviation > 0:
                sharpe = statistics.fmean(returns) / deviation * math.sqrt(len(returns))
        return PerformanceMetrics(
            initial_capital=initial_capital,
            final_equity=final_equity,
            total_return=final_equity / initial_capital - 1,
            trade_count=len(trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            expectancy=expectancy,
            sharpe_ratio=sharpe,
        )
