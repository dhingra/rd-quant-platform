from datetime import datetime, timezone
from pathlib import Path

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.automation import (
    AutomationConfig,
    AutomationMode,
    AutomationRunner,
    JsonlAutomationJournal,
)
from rdqp.execution import OrderManager, PaperExecutionBroker, SQLiteTradeJournal
from rdqp.risk import RiskLimits
from rdqp.strategies.domain.models import RuleOperator, StrategyDefinition, StrategyRule


def snap(symbol="AAPL", roc=0.02, rank=1):
    return FactorSnapshot(
        symbol,
        datetime.now(timezone.utc),
        100.0,
        1000,
        "Technology",
        roc,
        2.0,
        99.0,
        0.01,
        0.0,
        101,
        98,
        "inside",
        rank,
    )


def strategy():
    return StrategyDefinition(
        "auto",
        (StrategyRule("rank", RuleOperator.LTE, 2),),
        (StrategyRule("roc_pct", RuleOperator.LT, 0),),
    )


def manager(tmp_path: Path):
    broker = PaperExecutionBroker(100_000)
    broker.connect()
    return OrderManager(broker, SQLiteTradeJournal(tmp_path / "orders.db"))


def test_dry_run_does_not_submit(tmp_path):
    runner = AutomationRunner(manager(tmp_path))
    run = runner.run_cycle(
        strategy(), [snap()], AutomationConfig(mode=AutomationMode.DRY_RUN), RiskLimits()
    )
    assert run.decisions[0].action == "BUY"
    assert not run.decisions[0].submitted
    assert runner._orders.recent_orders() == ()


def test_paper_armed_submits(tmp_path):
    runner = AutomationRunner(manager(tmp_path))
    run = runner.run_cycle(
        strategy(), [snap()], AutomationConfig(mode=AutomationMode.PAPER_ARMED), RiskLimits()
    )
    assert run.decisions[0].submitted
    assert len(runner._orders.recent_orders()) == 1


def test_cooldown_deduplicates(tmp_path):
    runner = AutomationRunner(manager(tmp_path))
    cfg = AutomationConfig(mode=AutomationMode.DRY_RUN, cooldown_seconds=300)
    now = datetime.now(timezone.utc)
    runner.run_cycle(strategy(), [snap()], cfg, RiskLimits(), now)
    run = runner.run_cycle(strategy(), [snap()], cfg, RiskLimits(), now)
    assert run.decisions[0].action == "SKIP"


def test_jsonl_journal(tmp_path):
    journal = JsonlAutomationJournal(tmp_path / "automation.jsonl")
    runner = AutomationRunner(manager(tmp_path), journal)
    runner.run_cycle(
        strategy(), [snap()], AutomationConfig(mode=AutomationMode.DRY_RUN), RiskLimits()
    )
    assert journal.recent(1)[0]["strategy_name"] == "auto"
