from datetime import UTC, datetime

from rdqp.research.application.scorecard import ReadinessStatus, ScorecardEngine
from rdqp.strategies.domain.models import BacktestResult, EquityPoint, PerformanceMetrics


def test_scorecard_marks_strong_result_paper_ready() -> None:
    now = datetime.now(UTC)
    metrics = PerformanceMetrics(
        initial_capital=100_000,
        final_equity=120_000,
        total_return=0.20,
        trade_count=20,
        win_rate=0.60,
        profit_factor=1.8,
        max_drawdown=-0.10,
        expectancy=100.0,
        sharpe_ratio=1.4,
    )
    result = BacktestResult("Momentum", (), (EquityPoint(now, 100_000),), metrics)
    scorecard = ScorecardEngine().evaluate(result)
    assert scorecard.status is ReadinessStatus.PAPER_READY
    assert scorecard.score == 100
