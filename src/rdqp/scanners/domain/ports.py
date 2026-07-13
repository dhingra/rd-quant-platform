"""Scanner ports used by application services."""

from __future__ import annotations

from typing import Protocol

from rdqp.analytics.domain.models import FactorSnapshot
from rdqp.scanners.domain.models import ScanDefinition, ScannerAlert, ScanResult


class Scanner(Protocol):
    def run(self, definition: ScanDefinition, snapshots: list[FactorSnapshot]) -> ScanResult: ...


class ScanRepository(Protocol):
    def list(self) -> tuple[ScanDefinition, ...]: ...

    def save(self, definition: ScanDefinition) -> None: ...

    def delete(self, name: str) -> None: ...


class AlertSink(Protocol):
    def publish(self, alert: ScannerAlert) -> None: ...
