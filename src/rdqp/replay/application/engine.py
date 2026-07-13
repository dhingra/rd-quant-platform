"""Deterministic historical tick replay."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

from rdqp.market.domain.models import Tick


@dataclass(frozen=True, slots=True)
class ReplayProgress:
    processed: int
    total: int
    current_timestamp: datetime | None
    complete: bool


class ReplayEngine:
    """Replay normalized ticks in event-time order.

    The engine is deliberately UI-agnostic. Consumers provide a callback that receives
    batches, allowing the same component to drive the dashboard, scanners, or strategies.
    """

    def replay(
        self,
        ticks: Iterable[Tick],
        handler: Callable[[list[Tick]], None],
        *,
        batch_size: int = 100,
        speed: float = 0.0,
        progress: Callable[[ReplayProgress], None] | None = None,
    ) -> ReplayProgress:
        ordered = sorted(ticks, key=lambda tick: (tick.timestamp, tick.symbol))
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if speed < 0:
            raise ValueError("speed must be non-negative")

        total = len(ordered)
        processed = 0
        previous_time: datetime | None = None
        for start in range(0, total, batch_size):
            batch = ordered[start : start + batch_size]
            if speed > 0 and previous_time is not None and batch:
                delay = max(0.0, (batch[0].timestamp - previous_time).total_seconds() / speed)
                time.sleep(min(delay, 1.0))
            handler(batch)
            processed += len(batch)
            previous_time = batch[-1].timestamp if batch else previous_time
            state = ReplayProgress(processed, total, previous_time, processed == total)
            if progress is not None:
                progress(state)
        return ReplayProgress(processed, total, previous_time, True)
