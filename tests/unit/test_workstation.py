from datetime import UTC, datetime, timedelta

import pytest

from rdqp.market.domain.models import Tick
from rdqp.portfolio.domain.models import PaperPortfolioSnapshot, PaperPosition
from rdqp.strategies.domain.models import (
    BacktestResult,
    EquityPoint,
    PerformanceMetrics,
    TradeRecord,
)
from rdqp.workstation import (
    ReplayController,
    analyze_portfolio,
    build_performance_series,
    filter_trades,
    summarize_trades,
)


def backtest_result() -> BacktestResult:
    start = datetime(2026, 1, 30, tzinfo=UTC)
    equity = (
        EquityPoint(start, 100_000),
        EquityPoint(start + timedelta(days=1), 101_000),
        EquityPoint(start + timedelta(days=3), 99_000),
        EquityPoint(start + timedelta(days=32), 103_000),
    )
    trades = (
        TradeRecord("AAPL", start, start + timedelta(hours=2), 100, 105, 10, 50, 0.05, "target"),
        TradeRecord("MSFT", start, start + timedelta(hours=4), 200, 198, 5, -10, -0.01, "stop"),
    )
    metrics = PerformanceMetrics(100_000, 103_000, 0.03, 2, 0.5, 5.0, -0.0198, 20.0, 1.2)
    return BacktestResult("demo", trades, equity, metrics)


def test_performance_series_contains_drawdown_and_months() -> None:
    series = build_performance_series(backtest_result(), rolling_window=2)
    assert len(series.equity) == 4
    assert min(point.value for point in series.drawdown) < 0
    assert {(row.year, row.month) for row in series.monthly_returns} == {
        (2026, 1),
        (2026, 2),
        (2026, 3),
    }


def test_trade_summary_and_filtering() -> None:
    result = backtest_result()
    summary = summarize_trades(result.trades)
    assert summary.trade_count == 2
    assert summary.net_pnl == 40
    assert summary.win_rate == 0.5
    assert filter_trades(result.trades, symbol="aapl") == (result.trades[0],)
    with pytest.raises(ValueError):
        filter_trades(result.trades, winners_only=True, losers_only=True)


def test_portfolio_analytics_groups_sector_exposure() -> None:
    snapshot = PaperPortfolioSnapshot(
        10_000,
        4_000,
        (PaperPosition("AAPL", 10, 100, 110), PaperPosition("JPM", 5, 200, 220)),
        (),
    )
    analytics = analyze_portfolio(
        snapshot,
        lambda symbol: "Technology" if symbol == "AAPL" else "Financials",
    )
    assert analytics.equity == 6_200
    assert analytics.invested == 2_200
    assert len(analytics.allocations) == 2
    assert {item.label for item in analytics.sector_exposure} == {"Technology", "Financials"}


def test_replay_controller_orders_ticks_and_steps() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    ticks = [Tick("AAPL", start + timedelta(seconds=2), 102), Tick("AAPL", start, 100)]
    replay = ReplayController(ticks, speed=2)
    batches: list[tuple[Tick, ...]] = []
    replay.play()
    assert replay.step(lambda batch: batches.append(tuple(batch))) == 1
    assert batches[0][0].price == 100
    assert replay.state.cursor == 1
    replay.set_speed(5)
    assert replay.state.speed == 5
    replay.reset()
    assert replay.state.cursor == 0
