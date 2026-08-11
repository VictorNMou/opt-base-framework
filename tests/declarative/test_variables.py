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


def test_attach_to_model_applies_literal_bounds(tmp_path: Path) -> None:
    (tmp_path / "model_variables.yaml").write_text(
        "variables:\n  folga:\n    index: []\n    bounds: [0, 100]\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Variables().attach_to_model(model, data)

    assert model.folga.bounds == (0, 100)


def test_attach_to_model_applies_per_index_bounds_from_data(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n"
    )
    (tmp_path / "model_variables.yaml").write_text(
        "variables:\n"
        "  producao:\n"
        "    index: [PRODUTOS]\n"
        "    domain: NonNegativeReals\n"
        "    bounds: [0, data.capacidade_max]\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path),
        produtos=["p1", "p2"],
        capacidade_max={"p1": 10, "p2": 20},
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Variables().attach_to_model(model, data)

    assert model.producao["p1"].bounds == (0, 10)
    assert model.producao["p2"].bounds == (0, 20)


def test_attach_to_model_within_restricts_to_custom_set(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n  VALIDOS:\n    source: data.validos\n"
    )
    (tmp_path / "model_variables.yaml").write_text(
        "variables:\n  escolha:\n    index: [PRODUTOS]\n    within: VALIDOS\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path), produtos=["p1", "p2"], validos=["p1", "p2"]
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Variables().attach_to_model(model, data)

    assert model.escolha["p1"].domain is model.VALIDOS
