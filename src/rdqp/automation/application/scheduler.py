"""Single-process scheduler for guarded automation cycles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from rdqp.automation.domain.scheduling import SchedulerConfig, SessionDecision
from rdqp.notifications import Notification, NotificationRouter, NotificationSeverity


@dataclass(frozen=True, slots=True)
class SchedulerStatus:
    running: bool
    paused: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    consecutive_failures: int
    last_message: str


class AutomationScheduler:
    def __init__(
        self,
        config: SchedulerConfig,
        cycle: Callable[[], object],
        notifications: NotificationRouter | None = None,
    ) -> None:
        self.config = config
        self._cycle = cycle
        self._notifications = notifications
        self._running = False
        self._paused = False
        self._next_run_at: datetime | None = None
        self._last_run_at: datetime | None = None
        self._failures = 0
        self._last_message = "Scheduler created"

    def start(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        self._running = True
        self._next_run_at = now
        self._last_message = "Scheduler started"

    def stop(self) -> None:
        self._running = False
        self._next_run_at = None
        self._last_message = "Scheduler stopped"

    def pause(self) -> None:
        self._paused = True
        self._last_message = "Scheduler paused"

    def resume(self, now: datetime | None = None) -> None:
        self._paused = False
        self._next_run_at = now or datetime.now(timezone.utc)
        self._last_message = "Scheduler resumed"

    def run_due(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if not self._running or self._next_run_at is None or now < self._next_run_at:
            return False
        decision = self.config.session_policy.evaluate(now, paused=self._paused)
        if decision is not SessionDecision.ALLOWED:
            self._last_message = f"Cycle skipped: {decision.value}"
            self._next_run_at = now + timedelta(seconds=self.config.interval_seconds)
            return False
        try:
            self._cycle()
            self._last_run_at = now
            self._failures = 0
            self._last_message = "Cycle completed"
            self._next_run_at = now + timedelta(seconds=self.config.interval_seconds)
            return True
        except Exception as exc:
            self._failures += 1
            self._last_message = f"Cycle failed: {exc}"
            self._next_run_at = now + timedelta(seconds=self.config.interval_seconds)
            self._notify_failure(exc)
            if self._failures >= self.config.max_consecutive_failures:
                self.stop()
                self._last_message = "Scheduler stopped after repeated failures"
                self._notify_shutdown()
            return False

    def status(self) -> SchedulerStatus:
        return SchedulerStatus(
            running=self._running,
            paused=self._paused,
            next_run_at=self._next_run_at,
            last_run_at=self._last_run_at,
            consecutive_failures=self._failures,
            last_message=self._last_message,
        )

    def _notify_failure(self, exc: Exception) -> None:
        if self._notifications is None:
            return
        self._notifications.publish(Notification(
            category="automation",
            title="Automation cycle failed",
            message=str(exc),
            severity=NotificationSeverity.ERROR,
            dedupe_key="automation-cycle-failure",
        ))

    def _notify_shutdown(self) -> None:
        if self._notifications is None:
            return
        self._notifications.publish(Notification(
            category="automation",
            title="Automation scheduler stopped",
            message="Maximum consecutive failures reached.",
            severity=NotificationSeverity.CRITICAL,
            dedupe_key="automation-scheduler-stopped",
        ))
