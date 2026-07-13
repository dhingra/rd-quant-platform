"""Small in-process asynchronous event bus."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from rdqp.platform.eventbus.events import Event

E = TypeVar("E", bound=Event)
EventHandler = Callable[[Any], None | Awaitable[None]]


class EventBus:
    """Dispatch events to handlers registered for an event class.

    Handlers are invoked in subscription order. Synchronous and asynchronous
    handlers are supported. One failing handler does not prevent the remaining
    handlers from running; failures are logged and returned by ``publish``.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[EventHandler]] = defaultdict(list)
        self._logger = logging.getLogger(__name__)

    def subscribe(self, event_type: type[E], handler: Callable[[E], Any]) -> None:
        handlers = self._handlers[event_type]
        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(self, event_type: type[E], handler: Callable[[E], Any]) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: Event) -> list[BaseException]:
        failures: list[BaseException] = []
        for registered_type, handlers in tuple(self._handlers.items()):
            if not isinstance(event, registered_type):
                continue
            for handler in tuple(handlers):
                try:
                    result = handler(event)
                    if inspect.isawaitable(result):
                        await result
                except BaseException as exc:  # deliberate isolation boundary
                    failures.append(exc)
                    self._logger.exception("event handler failed", exc_info=exc)
        return failures

    def publish_nowait(self, event: Event) -> asyncio.Task[list[BaseException]]:
        return asyncio.create_task(self.publish(event))

    def clear(self) -> None:
        self._handlers.clear()
