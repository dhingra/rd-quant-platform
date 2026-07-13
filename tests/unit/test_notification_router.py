from datetime import datetime, timedelta, timezone

from rdqp.notifications import InMemoryNotificationSink, Notification, NotificationRouter


def test_router_deduplicates_within_cooldown() -> None:
    sink = InMemoryNotificationSink()
    router = NotificationRouter([sink], cooldown_seconds=60)
    now = datetime(2026, 7, 13, tzinfo=timezone.utc)
    notification = Notification("risk", "Blocked", "Order blocked", dedupe_key="risk-block")
    assert router.publish(notification, now)
    assert not router.publish(notification, now + timedelta(seconds=30))
    assert router.publish(notification, now + timedelta(seconds=61))
    assert len(sink.items) == 2
