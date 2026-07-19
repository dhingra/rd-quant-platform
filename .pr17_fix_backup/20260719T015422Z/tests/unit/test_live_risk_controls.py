from datetime import datetime, timedelta

from rdqp.execution import (
    AccountSnapshot,
    BrokerPosition,
    BrokerSyncHealth,
    ConnectionState,
    ExecutionMode,
    ExecutionOrderType,
    ExecutionSide,
    ExecutionStatus,
    ManagedOrder,
    OrderRequest,
)
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


def test_live_risk_normalizes_naive_timestamp_and_honors_pause() -> None:
    now = utc_now()
    account = AccountSnapshot("DU1", "USD", 10000, 1000, 1000, timestamp=now)
    health = BrokerSyncHealth(ConnectionState.CONNECTED, True, "ok", now, now)
    status = LiveRiskController().evaluate(
        account,
        LiveRiskLimits(),
        peak_net_liquidation=10000,
        health=health,
        market_data_timestamp=datetime.now(),
        emergency_paused=True,
    )
    assert not status.allowed
    assert "Emergency pause is active" in status.reasons


def test_live_risk_blocks_non_positive_equity_and_exact_duplicate() -> None:
    now = utc_now()
    request = OrderRequest(
        "AAPL",
        ExecutionSide.BUY,
        10,
        ExecutionOrderType.LIMIT,
        limit_price=100.0,
        strategy="momentum",
    )
    open_order = ManagedOrder(
        "o1",
        request,
        ExecutionMode.PAPER,
        ExecutionStatus.SUBMITTED,
    )
    account = AccountSnapshot("DU1", "USD", 0, 0, 0, timestamp=now)
    health = BrokerSyncHealth(ConnectionState.CONNECTED, True, "ok", now, now)
    status = LiveRiskController().evaluate(
        account,
        LiveRiskLimits(),
        peak_net_liquidation=0,
        health=health,
        market_data_timestamp=now,
        request=request,
        open_orders=(open_order,),
    )
    assert "Net liquidation is not positive" in status.reasons
    assert "Duplicate open order" in status.reasons
