"""Pre-trade risk checks independent of any broker implementation."""

from rdqp.execution.domain.models import AccountSnapshot, ExecutionSide, OrderRequest
from rdqp.risk.domain.models import RiskDecision, RiskLimits


class RiskEngine:
    def evaluate(
        self,
        request: OrderRequest,
        account: AccountSnapshot,
        limits: RiskLimits,
        open_order_count: int,
    ) -> RiskDecision:
        price = request.reference_price or request.limit_price or request.stop_price
        if price is None or price <= 0:
            return RiskDecision(False, "A positive reference price is required", 0.0)
        notional = price * request.quantity
        if limits.kill_switch:
            return RiskDecision(False, "Risk kill switch is enabled", notional)
        if open_order_count >= limits.max_open_orders:
            return RiskDecision(False, "Maximum open-order count reached", notional)
        if notional > limits.max_order_notional:
            return RiskDecision(False, "Order notional exceeds configured limit", notional)
        if request.quantity > limits.max_symbol_quantity:
            return RiskDecision(False, "Quantity exceeds configured symbol limit", notional)
        if account.realized_pnl + account.unrealized_pnl <= -limits.max_daily_loss:
            return RiskDecision(False, "Daily loss limit has been reached", notional)

        position = next((p for p in account.positions if p.symbol == request.symbol.upper()), None)
        current_quantity = 0.0 if position is None else position.quantity
        projected_quantity = (
            current_quantity + request.quantity
            if request.side is ExecutionSide.BUY
            else current_quantity - request.quantity
        )
        if projected_quantity < 0 and not limits.allow_short_selling:
            return RiskDecision(False, "Short selling is disabled", notional)
        if abs(projected_quantity * price) > limits.max_position_notional:
            return RiskDecision(
                False, "Projected position exceeds configured notional limit", notional
            )
        if request.side is ExecutionSide.BUY and notional > account.buying_power:
            return RiskDecision(False, "Insufficient buying power", notional)
        return RiskDecision(True, "Approved", notional)
