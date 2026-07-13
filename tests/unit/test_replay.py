from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from rdqp.market.domain.models import Tick
from rdqp.replay import CsvTickStore, ReplayEngine


def sample_ticks() -> list[Tick]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        Tick("MSFT", start + timedelta(seconds=2), 102.0, 20, "test"),
        Tick("AAPL", start, 100.0, 10, "test"),
        Tick("AAPL", start + timedelta(seconds=1), 101.0, 15, "test"),
    ]


def test_csv_tick_store_round_trip(tmp_path: Path) -> None:
    store = CsvTickStore()
    path = tmp_path / "session.csv"
    assert store.save(path, sample_ticks()) == 3
    loaded = store.load(path)
    assert [tick.symbol for tick in loaded] == ["AAPL", "AAPL", "MSFT"]
    assert loaded[-1].price == 102.0


def test_replay_orders_and_batches_ticks() -> None:
    received: list[Tick] = []
    result = ReplayEngine().replay(sample_ticks(), received.extend, batch_size=2)
    assert result.complete
    assert result.processed == 3
    assert [tick.price for tick in received] == [100.0, 101.0, 102.0]


def test_replay_rejects_invalid_batch_size() -> None:
    with pytest.raises(ValueError):
        ReplayEngine().replay([], lambda _: None, batch_size=0)
