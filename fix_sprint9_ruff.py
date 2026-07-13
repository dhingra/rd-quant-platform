#!/usr/bin/env python3
"""Apply the known Sprint 9 Ruff fixes to the current repository."""

from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected text not found in {path}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def patch_streamlit() -> None:
    path = ROOT / "apps/terminal/streamlit_app.py"
    text = path.read_text(encoding="utf-8")
    marker = '"""RD Quant Terminal — Sprint 9 cumulative research and automation platform."""\n'
    pragma = "# ruff: noqa: E402, E501\n"
    if pragma not in text:
        if marker not in text:
            raise RuntimeError(f"Expected module docstring not found in {path}")
        text = text.replace(marker, marker + pragma, 1)
    path.write_text(text, encoding="utf-8")


def patch_sqlite_state() -> None:
    path = ROOT / "src/rdqp/automation/infrastructure/sqlite_state.py"
    old = '''            conn.execute(
                "CREATE TABLE IF NOT EXISTS automation_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
'''
    new = '''            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
'''
    replace_exact(path, old, new)


def patch_yahoo_provider() -> None:
    path = ROOT / "src/rdqp/datasources/yahoo/provider.py"
    old = '''                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    else:
                        dt = dt.astimezone(UTC)
'''
    new = '''                    dt = (
                        dt.replace(tzinfo=UTC)
                        if dt.tzinfo is None
                        else dt.astimezone(UTC)
                    )
'''
    replace_exact(path, old, new)


def patch_walk_forward() -> None:
    path = ROOT / "src/rdqp/research/application/walk_forward.py"
    text = path.read_text(encoding="utf-8")
    if "from dataclasses import replace\n" not in text:
        text = text.replace(
            "from collections.abc import Mapping, Sequence\n",
            "from collections.abc import Mapping, Sequence\nfrom dataclasses import replace\n",
            1,
        )
    old = '''            candidate = optimized.best_trial.result
            selected = optimized.best_trial.parameters
            from dataclasses import replace

            configured = replace(definition, **selected)
'''
    new = '''            selected = optimized.best_trial.parameters
            configured = replace(definition, **selected)
'''
    if old in text:
        text = text.replace(old, new, 1)
    else:
        text = text.replace("            candidate = optimized.best_trial.result\n", "", 1)
        text = text.replace("            from dataclasses import replace\n\n", "", 1)
    path.write_text(text, encoding="utf-8")


def patch_research_repository() -> None:
    path = ROOT / "src/rdqp/research/infrastructure/sqlite_repository.py"
    text = path.read_text(encoding="utf-8")
    old_insert = '''            cursor = connection.execute(
                "INSERT INTO research_experiments(name,created_at,strategy_json,objective,parameters_json,metrics_json,notes) VALUES(?,?,?,?,?,?,?)",
'''
    new_insert = '''            cursor = connection.execute(
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
'''
    text = text.replace(old_insert, new_insert, 1)
    old_select = '''            rows = connection.execute(
                "SELECT id,name,created_at,strategy_json,objective,parameters_json,metrics_json,notes FROM research_experiments ORDER BY id DESC LIMIT ?",
'''
    new_select = '''            rows = connection.execute(
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
'''
    text = text.replace(old_select, new_select, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    required = [
        ROOT / "apps/terminal/streamlit_app.py",
        ROOT / "src/rdqp/automation/infrastructure/sqlite_state.py",
        ROOT / "src/rdqp/datasources/yahoo/provider.py",
        ROOT / "src/rdqp/research/application/walk_forward.py",
        ROOT / "src/rdqp/research/infrastructure/sqlite_repository.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Run this script from the repository root. Missing:\n" + "\n".join(missing))

    patch_streamlit()
    patch_sqlite_state()
    patch_yahoo_provider()
    patch_walk_forward()
    patch_research_repository()

    print("Applied Sprint 9 Ruff fixes.")
    print("Now run:")
    print("  python -m ruff format src tests apps")
    print("  python -m ruff check src tests apps --fix")
    print("  python -m ruff check src tests apps")


if __name__ == "__main__":
    main()
