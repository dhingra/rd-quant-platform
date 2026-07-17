"""Ports used by the broker account synchronization service."""

from __future__ import annotations

from typing import Protocol

from rdqp.execution.account_sync.models import BrokerAccountState


class BrokerAccountReader(Protocol):
    @property
    def name(self) -> str: ...

    def is_connected(self) -> bool: ...

    def read_account_state(self) -> BrokerAccountState: ...
