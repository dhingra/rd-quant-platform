import pytest

from rdqp.platform.plugins.registry import PluginRegistry


def test_registry_registers_and_lists_plugins() -> None:
    registry = PluginRegistry()

    class Demo: ...

    registry.register("indicator", "ROC", Demo)
    assert registry.get("indicator", "roc") is Demo
    assert registry.list("indicator") == ("roc",)


def test_registry_rejects_duplicate_plugin() -> None:
    registry = PluginRegistry()

    class Demo: ...

    registry.register("indicator", "roc", Demo)
    with pytest.raises(ValueError):
        registry.register("indicator", "roc", Demo)
