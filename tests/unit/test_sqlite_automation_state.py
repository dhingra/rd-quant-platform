from rdqp.automation import SQLiteAutomationStateStore


def test_state_store_round_trip(tmp_path) -> None:
    store = SQLiteAutomationStateStore(tmp_path / "state.sqlite3")
    store.set("mode", {"value": "PAUSED", "count": 2})
    assert store.get("mode") == {"value": "PAUSED", "count": 2}
    store.delete("mode")
    assert store.get("mode", "missing") == "missing"
