"""Immutable broker-account synchronization records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from rdqp.execution.domain.models import AccountSnapshot, ExecutionFill, ManagedOrder, utc_now


class ConnectionState(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    STALE = "STALE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class BrokerSyncHealth:
    state: ConnectionState
    connected: bool
    message: str
    last_success_at: datetime | None = None
    checked_at: datetime = field(default_factory=utc_now)
    stale_after_seconds: int = 30

    @property
    def age_seconds(self) -> float | None:
        if self.last_success_at is None:
            return None
        return max(0.0, (self.checked_at - self.last_success_at).total_seconds())

    @property
    def is_stale(self) -> bool:
        age = self.age_seconds
        return age is not None and age > self.stale_after_seconds


@dataclass(frozen=True, slots=True)
class BrokerAccountState:
    account: AccountSnapshot
    open_orders: tuple[ManagedOrder, ...] = ()
    executions: tuple[ExecutionFill, ...] = ()
    synchronized_at: datetime = field(default_factory=utc_now)
    source: str = "ibkr-paper"


@dataclass(frozen=True, slots=True)
class AccountSyncResult:
    state: BrokerAccountState | None
    health: BrokerSyncHealth
    duration_ms: float

    @property
    def succeeded(self) -> bool:
        return self.state is not None and self.health.state is ConnectionState.CONNECTED


def stale_health(
    last_success_at: datetime,
    *,
    stale_after: timedelta,
    checked_at: datetime | None = None,
) -> BrokerSyncHealth:
    checked = checked_at or utc_now()
    return BrokerSyncHealth(
        state=ConnectionState.STALE,
        connected=True,
        message="Broker data is stale",
        last_success_at=last_success_at,
        checked_at=checked,
        stale_after_seconds=max(1, int(stale_after.total_seconds())),
    )
