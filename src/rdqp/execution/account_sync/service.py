"""Application service for resilient broker-account synchronization."""

from __future__ import annotations

from datetime import datetime, timedelta
from time import perf_counter

from rdqp.execution.account_sync.models import (
    AccountSyncResult,
    BrokerSyncHealth,
    ConnectionState,
)
from rdqp.execution.account_sync.ports import BrokerAccountReader
from rdqp.execution.domain.models import utc_now


class AccountSyncService:
    def __init__(
        self,
        reader: BrokerAccountReader,
        *,
        stale_after: timedelta = timedelta(seconds=30),
    ) -> None:
        if stale_after.total_seconds() <= 0:
            raise ValueError("stale_after must be positive")
        self._reader = reader
        self._stale_after = stale_after
        self._last_success_at: datetime | None = None

    def synchronize(self) -> AccountSyncResult:
        started = perf_counter()
        checked_at = utc_now()

        if not self._reader.is_connected():
            health = BrokerSyncHealth(
                state=ConnectionState.DISCONNECTED,
                connected=False,
                message=f"{self._reader.name} is disconnected",
                last_success_at=self._last_success_at,
                checked_at=checked_at,
                stale_after_seconds=int(self._stale_after.total_seconds()),
            )
            return AccountSyncResult(None, health, self._elapsed_ms(started))

        try:
            state = self._reader.read_account_state()
        except Exception as exc:
            health = BrokerSyncHealth(
                state=ConnectionState.ERROR,
                connected=True,
                message=f"Account synchronization failed: {exc}",
                last_success_at=self._last_success_at,
                checked_at=checked_at,
                stale_after_seconds=int(self._stale_after.total_seconds()),
            )
            return AccountSyncResult(None, health, self._elapsed_ms(started))

        self._last_success_at = state.synchronized_at
        age = checked_at - state.synchronized_at
        connection_state = (
            ConnectionState.STALE if age > self._stale_after else ConnectionState.CONNECTED
        )
        message = "Broker account synchronized"
        if connection_state is ConnectionState.STALE:
            message = "Broker account response is stale"

        health = BrokerSyncHealth(
            state=connection_state,
            connected=True,
            message=message,
            last_success_at=state.synchronized_at,
            checked_at=checked_at,
            stale_after_seconds=int(self._stale_after.total_seconds()),
        )
        return AccountSyncResult(state, health, self._elapsed_ms(started))

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return (perf_counter() - started) * 1_000
