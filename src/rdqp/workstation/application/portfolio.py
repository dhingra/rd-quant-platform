"""Portfolio allocation and sector-exposure analytics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from rdqp.portfolio.domain.models import PaperPortfolioSnapshot
from rdqp.workstation.domain.models import PortfolioAnalytics, PortfolioSlice


def analyze_portfolio(
    snapshot: PaperPortfolioSnapshot,
    sector_for: Callable[[str], str] | None = None,
) -> PortfolioAnalytics:
    equity = snapshot.equity
    allocations = tuple(
        PortfolioSlice(
            position.symbol,
            position.market_value,
            position.market_value / equity if equity else 0.0,
        )
        for position in sorted(snapshot.positions, key=lambda item: item.market_value, reverse=True)
    )
    sectors: dict[str, float] = defaultdict(float)
    for position in snapshot.positions:
        sector = sector_for(position.symbol) if sector_for else "Unclassified"
        sectors[sector] += position.market_value
    sector_exposure = tuple(
        PortfolioSlice(label, value, value / equity if equity else 0.0)
        for label, value in sorted(sectors.items(), key=lambda item: item[1], reverse=True)
    )
    return PortfolioAnalytics(
        equity=equity,
        cash=snapshot.cash,
        invested=snapshot.market_value,
        realized_pnl=snapshot.realized_pnl,
        unrealized_pnl=snapshot.unrealized_pnl,
        allocations=allocations,
        sector_exposure=sector_exposure,
    )
