import pytest

from rdqp.execution import IBKRPaperBroker


def test_ibkr_broker_rejects_live_port():
    with pytest.raises(ValueError):
        IBKRPaperBroker("127.0.0.1", 7496, 7)


def test_ibkr_broker_accepts_standard_paper_ports():
    assert IBKRPaperBroker("127.0.0.1", 7497, 7).name == "ibkr-paper"
    assert IBKRPaperBroker("127.0.0.1", 4002, 7).name == "ibkr-paper"
