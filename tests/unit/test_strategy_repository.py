from rdqp.strategies import RuleOperator, StrategyDefinition, StrategyRule
from rdqp.strategies.infrastructure import YamlStrategyRepository


def test_strategy_repository_round_trip(tmp_path):
    repo = YamlStrategyRepository(tmp_path / "strategies.yaml")
    item = StrategyDefinition("Alpha", (StrategyRule("roc_pct", RuleOperator.GT, 1.0),))
    repo.save(item)
    loaded = repo.list()
    assert loaded[0].name == "Alpha"
    assert loaded[0].entry_rules[0].operator is RuleOperator.GT
    repo.delete("Alpha")
    assert repo.list() == ()
