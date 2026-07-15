"""Deterministic, UI-neutral replay playback controller."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from rdqp.market.domain.models import Tick
from rdqp.workstation.domain.models import ReplayState


class ReplayController:
    def __init__(self, ticks: Sequence[Tick], speed: float = 1.0) -> None:
        if speed <= 0:
            raise ValueError("speed must be positive")
        self._ticks = tuple(sorted(ticks, key=lambda tick: tick.timestamp))
        self._cursor = 0
        self._speed = float(speed)
        self._playing = False

    @property
    def state(self) -> ReplayState:
        return ReplayState(self._cursor, len(self._ticks), self._speed, self._playing)

    def play(self) -> None:
        self._playing = True

    def pause(self) -> None:
        self._playing = False

    def set_speed(self, speed: float) -> None:
        if speed <= 0:
            raise ValueError("speed must be positive")
        self._speed = float(speed)

    def reset(self) -> None:
        self._cursor = 0
        self._playing = False

    def step(self, handler: Callable[[Sequence[Tick]], object], count: int = 1) -> int:
        if count < 1:
            raise ValueError("count must be positive")
        end = min(len(self._ticks), self._cursor + count)
        batch = self._ticks[self._cursor : end]
        if batch:
            handler(batch)
            self._cursor = end
        if self._cursor >= len(self._ticks):
            self._playing = False
        return len(batch)
