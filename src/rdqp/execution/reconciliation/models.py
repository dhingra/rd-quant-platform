from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReconciliationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ReconciliationIssueType(StrEnum):
    MISSING_LOCAL_POSITION = "MISSING_LOCAL_POSITION"
    MISSING_BROKER_POSITION = "MISSING_BROKER_POSITION"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    AVERAGE_COST_MISMATCH = "AVERAGE_COST_MISMATCH"
    ORPHAN_LOCAL_ORDER = "ORPHAN_LOCAL_ORDER"


@dataclass(frozen=True, slots=True)
class ReconciliationIssue:
    issue_type: ReconciliationIssueType
    severity: ReconciliationSeverity
    symbol: str
    message: str
    broker_value: float | str | None = None
    local_value: float | str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    issues: tuple[ReconciliationIssue, ...]
    broker_position_count: int
    local_position_count: int
    broker_order_count: int
    local_order_count: int

    @property
    def is_reconciled(self) -> bool:
        return not any(i.severity is ReconciliationSeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(i.severity is ReconciliationSeverity.ERROR for i in self.issues)
