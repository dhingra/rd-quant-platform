"""Immutable automation-domain records."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class AutomationMode(StrEnum):
    DISABLED = "DISABLED"
    DRY_RUN = "DRY_RUN"
    PAPER_ARMED = "PAPER_ARMED"


@dataclass(frozen=True, slots=True)
class AutomationConfig:
    mode: AutomationMode = AutomationMode.DISABLED
    quantity: int = 10
    max_orders_per_cycle: int = 3
    max_open_positions: int = 5
    cooldown_seconds: int = 300
    require_positive_roc: bool = True
    allow_exits: bool = True

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.max_orders_per_cycle < 0 or self.max_open_positions < 0:
            raise ValueError("automation limits cannot be negative")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")


@dataclass(frozen=True, slots=True)
class AutomationDecision:
    symbol: str
    action: str
    reason: str
    submitted: bool = False
    order_id: str | None = None


@dataclass(frozen=True, slots=True)
class AutomationRun:
    strategy_name: str
    mode: AutomationMode
    evaluated: int
    decisions: tuple[AutomationDecision, ...]
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
