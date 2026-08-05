from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo

from optframework.declarative.expressions import Expressions
from optframework.declarative.sets import Sets


class _ExpressionRules:
    """Rules fake: uma expression escalar e uma indexada, reaproveitando Vars do modelo."""

    def __init__(self, data: object) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def dobro_x(self, model: pyo.ConcreteModel) -> object:
        return 2 * model.x

    def volume(self, model: pyo.ConcreteModel, produto: str) -> object:
        return 2 * model.producao[produto]


def test_attach_to_model_creates_scalar_expression(tmp_path: Path) -> None:
    (tmp_path / "model_expressions.yaml").write_text(
        "rules_class: tests.declarative.test_expressions._ExpressionRules\n"
        "expressions:\n  dobro_x: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.x.fix(3)

    Expressions().attach_to_model(model, data)

    assert isinstance(model.dobro_x, pyo.Expression)
    assert pyo.value(model.dobro_x) == 6


def test_attach_to_model_creates_indexed_expression(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n"
    )
    (tmp_path / "model_expressions.yaml").write_text(
        "rules_class: tests.declarative.test_expressions._ExpressionRules\n"
        "expressions:\n  volume:\n    index: [PRODUTOS]\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path), produtos=["p1", "p2"])
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)
    model.producao = pyo.Var(model.PRODUTOS, domain=pyo.NonNegativeReals)
    model.producao["p1"].fix(5)
    model.producao["p2"].fix(10)

    Expressions().attach_to_model(model, data)

    assert isinstance(model.volume, pyo.Expression)
    assert pyo.value(model.volume["p1"]) == 10
    assert pyo.value(model.volume["p2"]) == 20


def test_attach_to_model_without_config_file_is_a_no_op(tmp_path: Path) -> None:
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Expressions().attach_to_model(model, data)

    assert list(model.component_objects(pyo.Expression)) == []
