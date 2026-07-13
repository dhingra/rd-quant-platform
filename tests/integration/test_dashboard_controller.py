from rdqp.dashboard.application.controller import DashboardController


def test_simulator_dashboard_pipeline_produces_ranked_records() -> None:
    controller = DashboardController(["AAPL", "MSFT", "NVDA"], roc_window_seconds=10, seed=1)
    controller.simulator_refresh(20)
    records = controller.records()

    assert len(records) == 3
    assert all(record.roc is not None for record in records)
    assert {record.rank for record in records} == {1, 2, 3}
    assert controller.statistics().count == 3
    assert controller.symbol_history("AAPL")
