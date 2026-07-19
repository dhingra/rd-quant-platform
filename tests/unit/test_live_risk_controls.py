from datetime import timedelta

from rdqp.execution import AccountSnapshot, BrokerPosition, BrokerSyncHealth, ConnectionState
from rdqp.execution.domain.models import utc_now
from rdqp.risk.application.live_controls import LiveRiskController, LiveRiskLimits


def test_live_risk_blocks_stale_or_overexposed_account() -> None:
    now = utc_now()
    account = AccountSnapshot(
        "DU1",
        "USD",
        10000,
        1000,
        1000,
        positions=(BrokerPosition("AAPL", 100, 100, 100),),
        timestamp=now,
    )
    health = BrokerSyncHealth(ConnectionState.CONNECTED, True, "ok", now, now)
    status = LiveRiskController().evaluate(
        account,
        LiveRiskLimits(max_gross_exposure_pct=0.5),
        peak_net_liquidation=10000,
        health=health,
        market_data_timestamp=now - timedelta(minutes=1),
    )
    assert not status.allowed
    assert "Gross exposure limit exceeded" in status.reasons
    assert "Market data is stale" in status.reasons
