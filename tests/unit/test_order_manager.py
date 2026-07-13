from rdqp.execution import (
    ExecutionSide,
    OrderManager,
    OrderRequest,
    PaperExecutionBroker,
    SQLiteTradeJournal,
)
from rdqp.risk import RiskLimits


def test_order_manager_journals_fill(tmp_path):
    broker = PaperExecutionBroker(initial_cash=10_000)
    broker.connect()
    journal = SQLiteTradeJournal(tmp_path / "journal.sqlite3")
    manager = OrderManager(broker, journal)
    result = manager.submit(
        OrderRequest("AAPL", ExecutionSide.BUY, 10, reference_price=100),
        RiskLimits(max_order_notional=5_000),
        {"AAPL": 100},
    )
    assert result.status.value == "FILLED"
    assert journal.recent_orders()[0].order_id == result.order_id
    assert journal.recent_fills()[0].symbol == "AAPL"


def test_order_manager_journals_rejection(tmp_path):
    broker = PaperExecutionBroker(initial_cash=10_000)
    broker.connect()
    journal = SQLiteTradeJournal(tmp_path / "journal.sqlite3")
    manager = OrderManager(broker, journal)
    result = manager.submit(
        OrderRequest("AAPL", ExecutionSide.BUY, 100, reference_price=100),
        RiskLimits(max_order_notional=1_000),
        {"AAPL": 100},
    )
    assert result.status.value == "REJECTED"
    assert journal.recent_orders()[0].status.value == "REJECTED"
