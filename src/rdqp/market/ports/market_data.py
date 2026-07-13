"""Market-data provider port."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence

from rdqp.market.domain.models import Tick


class MarketDataProvider(ABC):
    """Abstraction implemented by all live, delayed, and simulated feeds."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider name."""

    @abstractmethod
    async def connect(self) -> None:
        """Open provider resources."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close provider resources."""

    @abstractmethod
    async def subscribe(self, symbols: Sequence[str]) -> None:
        """Subscribe to a collection of symbols."""

    @abstractmethod
    def stream(self) -> AsyncIterator[Tick]:
        """Yield normalized tick events."""
