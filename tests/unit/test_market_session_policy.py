from datetime import UTC, datetime, time

from rdqp.automation import MarketSessionPolicy, SessionDecision


def test_session_policy_allows_regular_session() -> None:
    policy = MarketSessionPolicy(start_time=time(9, 30), end_time=time(16, 0))
    instant = datetime(2026, 7, 13, 14, 0, tzinfo=UTC)  # 10:00 New York EDT
    assert policy.evaluate(instant) is SessionDecision.ALLOWED


def test_session_policy_blocks_weekend() -> None:
    policy = MarketSessionPolicy()
    instant = datetime(2026, 7, 11, 15, 0, tzinfo=UTC)
    assert policy.evaluate(instant) is SessionDecision.WEEKEND
