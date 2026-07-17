from datetime import timedelta

from rdqp.execution.account_sync import (
    AccountSyncService,
    BrokerAccountState,
    ConnectionState,
    IBKRAccountReader,
)
from rdqp.execution.domain.models import AccountSnapshot, utc_now


class FakeReader:
    name = "fake-broker"

    def __init__(self, *, connected: bool = True, fail: bool = False, stale: bool = False) -> None:
        self.connected = connected
        self.fail = fail
        self.stale = stale

    def is_connected(self) -> bool:
        return self.connected

    def read_account_state(self) -> BrokerAccountState:
        if self.fail:
            raise RuntimeError("boom")
        timestamp = utc_now() - timedelta(minutes=5) if self.stale else utc_now()
        return BrokerAccountState(
            account=AccountSnapshot("PAPER", "USD", 100_000, 50_000, 100_000),
            synchronized_at=timestamp,
            source=self.name,
        )


def test_account_sync_success() -> None:
    result = AccountSyncService(FakeReader()).synchronize()

    assert result.succeeded
    assert result.state is not None
    assert result.health.state is ConnectionState.CONNECTED
    assert result.duration_ms >= 0


def test_account_sync_disconnected() -> None:
    result = AccountSyncService(FakeReader(connected=False)).synchronize()

    assert result.state is None
    assert result.health.state is ConnectionState.DISCONNECTED
    assert not result.health.connected


def test_account_sync_error_is_reported() -> None:
    result = AccountSyncService(FakeReader(fail=True)).synchronize()

    assert result.state is None
    assert result.health.state is ConnectionState.ERROR
    assert "boom" in result.health.message


def test_account_sync_detects_stale_state() -> None:
    result = AccountSyncService(
        FakeReader(stale=True),
        stale_after=timedelta(seconds=30),
    ).synchronize()

    assert result.state is not None
    assert result.health.state is ConnectionState.STALE
    assert not result.succeeded


def test_ibkr_reader_rejects_live_ports() -> None:
    try:
        IBKRAccountReader("127.0.0.1", 7496, 7)
    except ValueError as exc:
        assert "paper port" in str(exc)
    else:
        raise AssertionError("Expected live-port rejection")
