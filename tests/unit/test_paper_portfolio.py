from rdqp.portfolio import PaperPortfolio


def test_paper_portfolio_buy_mark_sell():
    portfolio = PaperPortfolio(10_000)
    portfolio.buy("AAPL", 10, 100)
    portfolio.mark({"AAPL": 110})
    snap = portfolio.snapshot()
    assert snap.unrealized_pnl == 100
    portfolio.sell("AAPL", 5, 110)
    snap = portfolio.snapshot()
    assert snap.realized_pnl == 50
    assert snap.positions[0].quantity == 5
