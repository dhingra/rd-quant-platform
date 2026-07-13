from rdqp.execution import AccountSnapshot, BrokerPosition, ExecutionSide, OrderRequest
from rdqp.risk import RiskEngine, RiskLimits


def account(**overrides):
    values = dict(
        account_id="TEST",
        currency="USD",
        net_liquidation=100_000,
        cash=50_000,
        buying_power=50_000,
        realized_pnl=0,
        unrealized_pnl=0,
        positions=(),
    )
    values.update(overrides)
    return AccountSnapshot(**values)


def test_risk_approves_valid_order():
    decision = RiskEngine().evaluate(
        OrderRequest("AAPL", ExecutionSide.BUY, 10, reference_price=200),
        account(),
        RiskLimits(),
        0,
    )
    assert decision.approved
    assert decision.estimated_notional == 2_000


def test_risk_rejects_notional_and_kill_switch():
    request = OrderRequest("AAPL", ExecutionSide.BUY, 100, reference_price=200)
    assert not RiskEngine().evaluate(request, account(), RiskLimits(max_order_notional=5_000), 0).approved
    assert not RiskEngine().evaluate(request, account(), RiskLimits(kill_switch=True), 0).approved


def test_risk_rejects_short_when_disabled():
    decision = RiskEngine().evaluate(
        OrderRequest("AAPL", ExecutionSide.SELL, 5, reference_price=200),
        account(),
        RiskLimits(allow_short_selling=False),
        0,
    )
    assert not decision.approved
