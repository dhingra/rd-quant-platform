from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from rdqp.execution.account_sync.models import BrokerSyncHealth, ConnectionState
from rdqp.execution.domain.models import AccountSnapshot, ManagedOrder, OrderRequest, utc_now


@dataclass(frozen=True, slots=True)
class LiveRiskLimits:
    max_daily_loss: float = 1_000.0
    max_drawdown_pct: float = 0.05
    max_gross_exposure_pct: float = 1.5
    max_symbol_concentration_pct: float = 0.25
    market_data_max_age: timedelta = timedelta(seconds=30)


@dataclass(frozen=True, slots=True)
class LiveRiskStatus:
    allowed: bool
    reasons: tuple[str, ...]
    gross_exposure: float
    drawdown_pct: float


class LiveRiskController:
    def evaluate(
        self,
        account: AccountSnapshot,
        limits: LiveRiskLimits,
        *,
        peak_net_liquidation: float,
        health: BrokerSyncHealth,
        market_data_timestamp: datetime,
        request: OrderRequest | None = None,
        open_orders: tuple[ManagedOrder, ...] = (),
    ) -> LiveRiskStatus:
        reasons: list[str] = []
        pnl = account.realized_pnl + account.unrealized_pnl
        if pnl <= -limits.max_daily_loss:
            reasons.append("Daily loss limit reached")
        drawdown = (
            0.0
            if peak_net_liquidation <= 0
            else max(0.0, (peak_net_liquidation - account.net_liquidation) / peak_net_liquidation)
        )
        if drawdown >= limits.max_drawdown_pct:
            reasons.append("Maximum drawdown reached")
        gross = sum(abs(p.market_value) for p in account.positions)
        gross_pct = 0.0 if account.net_liquidation <= 0 else gross / account.net_liquidation
        if gross_pct > limits.max_gross_exposure_pct:
            reasons.append("Gross exposure limit exceeded")
        if account.net_liquidation > 0 and any(
            abs(p.market_value) / account.net_liquidation > limits.max_symbol_concentration_pct
            for p in account.positions
        ):
            reasons.append("Symbol concentration limit exceeded")
        if health.state is not ConnectionState.CONNECTED:
            reasons.append("Broker connection is not healthy")
        if utc_now() - market_data_timestamp > limits.market_data_max_age:
            reasons.append("Market data is stale")
        if request is not None and any(
            o.request.symbol.upper() == request.symbol.upper()
            and o.request.side is request.side
            and o.status.value not in {"FILLED", "CANCELLED", "REJECTED", "ERROR"}
            for o in open_orders
        ):
            reasons.append("Possible duplicate open order")
        return LiveRiskStatus(not reasons, tuple(reasons), gross, drawdown)
