from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo

from optframework.declarative.sets import Sets
from optframework.declarative.variables import Variables


def test_attach_to_model_creates_indexed_variable_with_domain(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n  PERIODOS:\n    source: data.periodos\n"
    )
    (tmp_path / "model_variables.yaml").write_text(
        "variables:\n"
        "  producao:\n"
        "    index: [PRODUTOS, PERIODOS]\n"
        "    domain: NonNegativeReals\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path), produtos=["p1"], periodos=[1, 2])
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Variables().attach_to_model(model, data)

    assert sorted(model.producao.keys()) == [("p1", 1), ("p1", 2)]
    assert model.producao["p1", 1].domain is pyo.NonNegativeReals


def test_attach_to_model_scalar_variable_defaults_to_reals(tmp_path: Path) -> None:
    (tmp_path / "model_variables.yaml").write_text(
        "variables:\n  folga:\n    index: []\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Variables().attach_to_model(model, data)

    assert model.folga.domain is pyo.Reals
