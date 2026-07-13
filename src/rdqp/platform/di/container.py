"""Minimal dependency-injection container."""

from collections.abc import Callable
from typing import Any, TypeVar, cast

from rdqp.common.exceptions import DependencyResolutionError

T = TypeVar("T")
Factory = Callable[["Container"], Any]


class Container:
    """Registers factories and lazily resolves singleton services."""

    def __init__(self) -> None:
        self._factories: dict[object, Factory] = {}
        self._singletons: dict[object, object] = {}

    def register_instance(self, key: object, instance: object) -> None:
        self._singletons[key] = instance

    def register_factory(self, key: object, factory: Factory, *, singleton: bool = True) -> None:
        self._factories[key] = factory
        if not singleton:
            self._singletons.pop(key, None)
        setattr(factory, "_rdqp_singleton", singleton)

    def resolve(self, key: type[T] | str) -> T:
        if key in self._singletons:
            return cast(T, self._singletons[key])
        factory = self._factories.get(key)
        if factory is None:
            raise DependencyResolutionError(f"No dependency registered for {key!r}")
        instance = factory(self)
        if bool(getattr(factory, "_rdqp_singleton", True)):
            self._singletons[key] = instance
        return cast(T, instance)
