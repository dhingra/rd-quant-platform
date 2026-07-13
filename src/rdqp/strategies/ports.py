"""Strategy extension port."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from rdqp.market.domain.models import Signal


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(self, records: Sequence[dict[str, object]]) -> list[Signal]: ...
