"""Risk-policy value objects."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskLimits:
    max_order_notional: float = 10_000.0
    max_position_notional: float = 25_000.0
    max_daily_loss: float = 1_000.0
    max_open_orders: int = 10
    max_symbol_quantity: int = 1_000
    allow_short_selling: bool = False
    kill_switch: bool = False

    def __post_init__(self) -> None:
        if self.max_order_notional <= 0 or self.max_position_notional <= 0:
            raise ValueError("notional limits must be positive")
        if self.max_daily_loss <= 0:
            raise ValueError("max_daily_loss must be positive")
        if self.max_open_orders < 0 or self.max_symbol_quantity <= 0:
            raise ValueError("order and quantity limits are invalid")


@dataclass(frozen=True, slots=True)
class RiskDecision:
    approved: bool
    reason: str
    estimated_notional: float
