"""SQLite persistence for reproducible research experiments."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from rdqp.research.domain.models import ResearchExperiment
from rdqp.strategies.domain.models import RuleOperator, StrategyDefinition, StrategyRule


class SqliteExperimentRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS research_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                strategy_json TEXT NOT NULL,
                objective TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                notes TEXT NOT NULL
                )"""
            )

    def save(self, experiment: ResearchExperiment) -> int:
        strategy = asdict(experiment.strategy)
        for key in ("entry_rules", "exit_rules"):
            strategy[key] = [
                {"field": rule["field"], "operator": str(rule["operator"]), "value": rule["value"]}
                for rule in strategy[key]
            ]
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO research_experiments (
                    name,
                    created_at,
                    strategy_json,
                    objective,
                    parameters_json,
                    metrics_json,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment.name,
                    experiment.created_at.astimezone(UTC).isoformat(),
                    json.dumps(strategy),
                    experiment.objective,
                    json.dumps(experiment.parameters),
                    json.dumps(experiment.metrics),
                    experiment.notes,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return an experiment ID")
            return cursor.lastrowid

    def list(self, limit: int = 100) -> tuple[ResearchExperiment, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    created_at,
                    strategy_json,
                    objective,
                    parameters_json,
                    metrics_json,
                    notes
                FROM research_experiments
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._decode(row) for row in rows)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    @staticmethod
    def _decode(row: tuple[object, ...]) -> ResearchExperiment:
        strategy_raw = json.loads(str(row[3]))
        strategy = StrategyDefinition(
            name=strategy_raw["name"],
            entry_rules=tuple(
                StrategyRule(item["field"], RuleOperator(item["operator"]), item.get("value"))
                for item in strategy_raw["entry_rules"]
            ),
            exit_rules=tuple(
                StrategyRule(item["field"], RuleOperator(item["operator"]), item.get("value"))
                for item in strategy_raw["exit_rules"]
            ),
            initial_capital=float(strategy_raw["initial_capital"]),
            allocation_pct=float(strategy_raw["allocation_pct"]),
            commission_per_trade=float(strategy_raw["commission_per_trade"]),
            stop_loss_pct=strategy_raw.get("stop_loss_pct"),
            take_profit_pct=strategy_raw.get("take_profit_pct"),
            description=strategy_raw.get("description", ""),
        )
        return ResearchExperiment(
            id=int(str(row[0])),
            name=str(row[1]),
            created_at=datetime.fromisoformat(str(row[2])),
            strategy=strategy,
            objective=str(row[4]),
            parameters={key: float(value) for key, value in json.loads(str(row[5])).items()},
            metrics=json.loads(str(row[6])),
            notes=str(row[7]),
        )
