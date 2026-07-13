import pytest

from rdqp.common.exceptions import DependencyResolutionError
from rdqp.platform.di.container import Container


def test_container_resolves_singleton_factory() -> None:
    container = Container()
    container.register_factory("service", lambda _: object())
    assert container.resolve("service") is container.resolve("service")


def test_container_reports_missing_dependency() -> None:
    with pytest.raises(DependencyResolutionError):
        Container().resolve("missing")
