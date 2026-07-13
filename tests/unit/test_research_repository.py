from datetime import UTC, datetime

from rdqp.research.domain.models import ResearchExperiment
from rdqp.research.infrastructure.sqlite_repository import SqliteExperimentRepository
from rdqp.strategies.domain.models import RuleOperator, StrategyDefinition, StrategyRule


def test_experiment_round_trip(tmp_path) -> None:
    repo = SqliteExperimentRepository(tmp_path / "research.sqlite3")
    strategy = StrategyDefinition("Momentum", (StrategyRule("roc_pct", RuleOperator.GT, 1.0),))
    identifier = repo.save(
        ResearchExperiment(None, "trial", datetime.now(UTC), strategy, "sharpe_ratio", {"stop_loss_pct": 0.02}, {"total_return": 0.1}, "note")
    )
    loaded = repo.list()
    assert identifier == 1
    assert loaded[0].strategy.name == "Momentum"
    assert loaded[0].parameters["stop_loss_pct"] == 0.02
