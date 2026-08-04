import pytest

from optframework.strategy import registry
from optframework.strategy.milp_strategy import MilpStrategy


def test_milp_registered_on_package_import() -> None:
    """Importar optframework.strategy já executa strategy/__init__.py (registra 'milp')."""
    assert registry.get("milp") is MilpStrategy


def test_get_unregistered_type_raises_key_error() -> None:
    with pytest.raises(KeyError):
        registry.get("inexistente")


def test_register_and_get_custom_type() -> None:
    class DummyStrategy:
        pass

    registry.register("dummy", DummyStrategy)

    assert registry.get("dummy") is DummyStrategy
