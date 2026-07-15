"""Trade-explorer analytics."""

from __future__ import annotations

import statistics
from collections.abc import Iterable

from rdqp.strategies.domain.models import TradeRecord
from rdqp.workstation.domain.models import TradeSummary


def summarize_trades(trades: Iterable[TradeRecord]) -> TradeSummary:
    rows = tuple(trades)
    pnls = [trade.pnl for trade in rows]
    winners = [pnl for pnl in pnls if pnl > 0]
    losers = [pnl for pnl in pnls if pnl < 0]
    holding = [(trade.exit_time - trade.entry_time).total_seconds() / 3600 for trade in rows]
    return TradeSummary(
        trade_count=len(rows),
        winners=len(winners),
        losers=len(losers),
        win_rate=len(winners) / len(rows) if rows else 0.0,
        gross_profit=sum(winners),
        gross_loss=sum(losers),
        net_pnl=sum(pnls),
        average_pnl=statistics.fmean(pnls) if pnls else 0.0,
        median_pnl=statistics.median(pnls) if pnls else 0.0,
        average_holding_hours=statistics.fmean(holding) if holding else 0.0,
        best_trade=max(pnls, default=0.0),
        worst_trade=min(pnls, default=0.0),
    )


def filter_trades(
    trades: Iterable[TradeRecord],
    symbol: str | None = None,
    winners_only: bool = False,
    losers_only: bool = False,
) -> tuple[TradeRecord, ...]:
    if winners_only and losers_only:
        raise ValueError("winners_only and losers_only cannot both be true")
    normalized = symbol.upper() if symbol else None
    return tuple(
        trade
        for trade in trades
        if (normalized is None or trade.symbol.upper() == normalized)
        and (not winners_only or trade.pnl > 0)
        and (not losers_only or trade.pnl < 0)
    )
