"""Simple plugin registry for providers, indicators, scanners, and strategies."""

from collections import defaultdict
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T", bound=type[Any])


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, type[Any]]] = defaultdict(dict)

    def register(self, category: str, name: str, plugin: type[Any]) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("plugin name must not be empty")
        if normalized in self._plugins[category]:
            raise ValueError(f"duplicate plugin: {category}/{normalized}")
        self._plugins[category][normalized] = plugin

    def get(self, category: str, name: str) -> type[Any]:
        return self._plugins[category][name.strip().lower()]

    def list(self, category: str) -> tuple[str, ...]:
        return tuple(sorted(self._plugins[category]))


registry = PluginRegistry()


def plugin(category: str, name: str) -> Callable[[T], T]:
    def decorator(cls: T) -> T:
        registry.register(category, name, cls)
        return cls

    return decorator
