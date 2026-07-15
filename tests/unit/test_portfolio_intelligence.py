from rdqp.portfolio_intelligence import (
    OptimizationObjective,
    PortfolioConstraints,
    PortfolioOptimizer,
    StressScenario,
    analyze_risk,
    build_rebalance_plan,
    run_stress_tests,
)

RETURNS = {
    "AAPL": [0.01, -0.005, 0.012, 0.004, -0.002, 0.008],
    "MSFT": [0.006, -0.002, 0.009, 0.003, 0.001, 0.005],
    "JPM": [-0.002, 0.004, 0.001, 0.006, 0.003, -0.001],
}


def test_optimizer_produces_bounded_weights() -> None:
    result = PortfolioOptimizer().optimize(
        RETURNS,
        OptimizationObjective.MINIMUM_VOLATILITY,
        PortfolioConstraints(max_weight=0.7, iterations=300),
    )
    assert abs(sum(item.weight for item in result.weights) - 1.0) < 1e-6
    assert all(0 <= item.weight <= 0.7 for item in result.weights)
    assert result.volatility >= 0


def test_maximum_sharpe_solution() -> None:
    result = PortfolioOptimizer().optimize(
        RETURNS,
        OptimizationObjective.MAXIMUM_SHARPE,
        PortfolioConstraints(max_weight=0.8, iterations=300),
    )
    assert len(result.weights) == 3
    assert result.sharpe_ratio != 0


def test_risk_report_and_contributions() -> None:
    report = analyze_risk(RETURNS, {"AAPL": 0.4, "MSFT": 0.4, "JPM": 0.2})
    assert len(report.contributions) == 3
    assert abs(sum(item.percentage for item in report.contributions) - 1.0) < 1e-6
    assert report.value_at_risk_95 >= 0
    assert len(report.correlation) == 3


def test_stress_and_rebalance() -> None:
    weights = {"AAPL": 0.5, "MSFT": 0.5}
    results = run_stress_tests(
        weights, 100_000, [StressScenario("Crash", {"AAPL": -0.1, "MSFT": -0.2})]
    )
    assert results[0].pnl_value == -15_000

    plan = build_rebalance_plan(weights, {"AAPL": 0.4, "MSFT": 0.6}, 100_000, cost_bps=10)
    assert len(plan.trades) == 2
    assert abs(plan.turnover - 0.1) < 1e-12
    assert abs(plan.estimated_cost - 20) < 1e-9
