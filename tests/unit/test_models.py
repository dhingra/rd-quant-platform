from datetime import datetime, timezone

import pytest

from rdqp.market.domain.models import Portfolio, Position, Tick


def test_tick_requires_positive_price() -> None:
    with pytest.raises(ValueError):
        Tick("AAPL", datetime.now(timezone.utc), 0)


def test_tick_requires_aware_timestamp() -> None:
    with pytest.raises(ValueError):
        Tick("AAPL", datetime.now(), 100)


def test_portfolio_equity() -> None:
    portfolio = Portfolio(cash=1_000, positions=(Position("AAPL", 10, 90, 100),))
    assert portfolio.equity == 2_000
    assert portfolio.positions[0].unrealized_pnl == 100
