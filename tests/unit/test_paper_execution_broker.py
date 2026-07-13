from rdqp.execution import ExecutionSide, OrderRequest, PaperExecutionBroker


def test_paper_broker_fills_and_updates_account():
    broker = PaperExecutionBroker(initial_cash=10_000)
    broker.connect()
    order = broker.submit(
        "ORDER-1", OrderRequest("AAPL", ExecutionSide.BUY, 10, reference_price=100)
    )
    assert order.filled_quantity == 10
    snapshot = broker.account_snapshot({"AAPL": 105})
    assert snapshot.cash == 9_000
    assert snapshot.positions[0].quantity == 10
    assert snapshot.unrealized_pnl == 50


def test_paper_broker_realizes_profit_on_sell():
    broker = PaperExecutionBroker(initial_cash=10_000)
    broker.connect()
    broker.submit("BUY", OrderRequest("AAPL", ExecutionSide.BUY, 10, reference_price=100))
    broker.submit("SELL", OrderRequest("AAPL", ExecutionSide.SELL, 5, reference_price=110))
    snapshot = broker.account_snapshot()
    assert snapshot.realized_pnl == 50
    assert snapshot.positions[0].quantity == 5
