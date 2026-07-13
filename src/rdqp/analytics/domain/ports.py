"""Analytics extension ports."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from rdqp.market.domain.models import Tick

T = TypeVar("T")


class Indicator(ABC, Generic[T]):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def update(self, tick: Tick) -> T | None: ...


class Scanner(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def scan(self, records: Sequence[dict[str, object]]) -> list[dict[str, object]]: ...
