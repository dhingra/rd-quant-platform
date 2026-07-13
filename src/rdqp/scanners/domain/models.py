"""Scanner domain models and filter semantics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class FilterOperator(StrEnum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NE = "!="
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    CONTAINS = "contains"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"


@dataclass(frozen=True, slots=True)
class ScannerFilter:
    field: str
    operator: FilterOperator
    value: Any = None
    second_value: Any = None


@dataclass(frozen=True, slots=True)
class ScanDefinition:
    name: str
    filters: tuple[ScannerFilter, ...]
    sort_by: str = "roc"
    descending: bool = True
    limit: int = 50
    enabled: bool = True
    description: str = ""


@dataclass(frozen=True, slots=True)
class ScanMatch:
    symbol: str
    timestamp: datetime
    values: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ScanResult:
    definition: ScanDefinition
    matches: tuple[ScanMatch, ...]
    evaluated_count: int
    elapsed_ms: float
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class ScannerAlert:
    scan_name: str
    symbol: str
    triggered_at: datetime
    message: str
    values: dict[str, Any] = field(default_factory=dict)
