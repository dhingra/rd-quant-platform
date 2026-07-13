"""YAML persistence adapter for user-defined strategies."""

from __future__ import annotations

from pathlib import Path

import yaml

from rdqp.strategies.domain.models import RuleOperator, StrategyDefinition, StrategyRule


class YamlStrategyRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> tuple[StrategyDefinition, ...]:
        if not self.path.exists():
            return ()
        payload = yaml.safe_load(self.path.read_text()) or []
        return tuple(self._from_dict(item) for item in payload)

    def save(self, definition: StrategyDefinition) -> None:
        items = {item.name: item for item in self.list()}
        items[definition.name] = definition
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump([self._to_dict(item) for item in items.values()], sort_keys=False))

    def delete(self, name: str) -> None:
        items = [item for item in self.list() if item.name != name]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump([self._to_dict(item) for item in items], sort_keys=False))

    @staticmethod
    def _to_dict(item: StrategyDefinition) -> dict[str, object]:
        def rules(values: tuple[StrategyRule, ...]) -> list[dict[str, object]]:
            return [{"field": rule.field, "operator": rule.operator.value, "value": rule.value} for rule in values]
        return {
            "name": item.name,
            "description": item.description,
            "entry_rules": rules(item.entry_rules),
            "exit_rules": rules(item.exit_rules),
            "initial_capital": item.initial_capital,
            "allocation_pct": item.allocation_pct,
            "commission_per_trade": item.commission_per_trade,
            "stop_loss_pct": item.stop_loss_pct,
            "take_profit_pct": item.take_profit_pct,
        }

    @staticmethod
    def _from_dict(data: dict[str, object]) -> StrategyDefinition:
        def rules(key: str) -> tuple[StrategyRule, ...]:
            raw = data.get(key, [])
            return tuple(StrategyRule(str(x["field"]), RuleOperator(str(x["operator"])), x.get("value")) for x in raw)  # type: ignore[index,union-attr]
        return StrategyDefinition(
            name=str(data["name"]),
            description=str(data.get("description", "")),
            entry_rules=rules("entry_rules"),
            exit_rules=rules("exit_rules"),
            initial_capital=float(data.get("initial_capital", 100_000)),
            allocation_pct=float(data.get("allocation_pct", 0.10)),
            commission_per_trade=float(data.get("commission_per_trade", 0.0)),
            stop_loss_pct=None if data.get("stop_loss_pct") is None else float(data["stop_loss_pct"]),
            take_profit_pct=None if data.get("take_profit_pct") is None else float(data["take_profit_pct"]),
        )
