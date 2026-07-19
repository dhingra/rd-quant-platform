from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from rdqp.execution.account_sync.models import BrokerSyncHealth, ConnectionState
from rdqp.execution.domain.models import (
    AccountSnapshot,
    ManagedOrder,
    OrderRequest,
    utc_now,
)


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
        emergency_paused: bool = False,
    ) -> LiveRiskStatus:
        reasons: list[str] = []
        if emergency_paused:
            reasons.append("Emergency pause is active")

        pnl = account.realized_pnl + account.unrealized_pnl
        if pnl <= -limits.max_daily_loss:
            reasons.append("Daily loss limit reached")

        drawdown = (
            0.0
            if peak_net_liquidation <= 0
            else max(
                0.0,
                (peak_net_liquidation - account.net_liquidation)
                / peak_net_liquidation,
            )
        )
        if drawdown >= limits.max_drawdown_pct:
            reasons.append("Maximum drawdown reached")

        gross = sum(abs(position.market_value) for position in account.positions)
        if account.net_liquidation <= 0:
            reasons.append("Net liquidation is not positive")
        else:
            gross_pct = gross / account.net_liquidation
            if gross_pct > limits.max_gross_exposure_pct:
                reasons.append("Gross exposure limit exceeded")
            if any(
                abs(position.market_value) / account.net_liquidation
                > limits.max_symbol_concentration_pct
                for position in account.positions
            ):
                reasons.append("Symbol concentration limit exceeded")

        if health.state is not ConnectionState.CONNECTED:
            reasons.append("Broker connection is not healthy")

        timestamp = self._aware_utc(market_data_timestamp)
        if utc_now() - timestamp > limits.market_data_max_age:
            reasons.append("Market data is stale")

        if request is not None:
            fingerprint = self._request_fingerprint(request)
            if any(
                self._request_fingerprint(order.request) == fingerprint
                and order.status.value
                not in {"FILLED", "CANCELLED", "REJECTED", "ERROR"}
                for order in open_orders
            ):
                reasons.append("Duplicate open order")

        return LiveRiskStatus(not reasons, tuple(reasons), gross, drawdown)

    @staticmethod
    def _aware_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _request_fingerprint(request: OrderRequest) -> tuple[object, ...]:
        return (
            request.symbol.strip().upper(),
            request.side,
            request.quantity,
            request.order_type,
            request.limit_price,
            request.stop_price,
            request.strategy,
        )
