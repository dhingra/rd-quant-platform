# Coding Standards

- Python 3.11+
- type annotations on public APIs
- immutable domain values where practical
- no market calculations in UI modules
- no infrastructure imports inside domain modules
- composition over inheritance except for small ports/ABCs
- explicit UTC-aware timestamps
- tests for behavior and failure boundaries
- Ruff, Black, mypy, pytest, and pre-commit
