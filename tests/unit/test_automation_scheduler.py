from datetime import datetime, time, timedelta, timezone

from rdqp.automation import AutomationScheduler, MarketSessionPolicy, SchedulerConfig


def always_open() -> MarketSessionPolicy:
    return MarketSessionPolicy(timezone_name="UTC", start_time=time(0, 0), end_time=time(23, 59), weekdays_only=False)


def test_scheduler_runs_due_cycle() -> None:
    calls: list[int] = []
    scheduler = AutomationScheduler(SchedulerConfig(10, 3, always_open()), lambda: calls.append(1))
    now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
    scheduler.start(now)
    assert scheduler.run_due(now)
    assert calls == [1]
    assert not scheduler.run_due(now + timedelta(seconds=5))


def test_scheduler_stops_after_failure_threshold() -> None:
    def fail() -> None:
        raise RuntimeError("boom")

    scheduler = AutomationScheduler(SchedulerConfig(1, 2, always_open()), fail)
    now = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)
    scheduler.start(now)
    assert not scheduler.run_due(now)
    assert not scheduler.run_due(now + timedelta(seconds=1))
    assert not scheduler.status().running
    assert scheduler.status().consecutive_failures == 2
