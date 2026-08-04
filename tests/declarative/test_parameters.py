from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo

from optframework.declarative.parameters import Parameters
from optframework.declarative.sets import Sets


def test_attach_to_model_creates_indexed_parameter(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n"
    )
    (tmp_path / "model_parameters.yaml").write_text(
        "parameters:\n"
        "  custo:\n"
        "    index: [PRODUTOS]\n"
        "    source: data.custo_unitario\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path),
        produtos=["p1", "p2"],
        custo_unitario={"p1": 10.0, "p2": 20.0},
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Parameters().attach_to_model(model, data)

    assert model.custo.extract_values() == {"p1": 10.0, "p2": 20.0}
    assert not model.custo.mutable


def test_attach_to_model_respects_mutable_flag(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PERIODOS:\n    source: data.periodos\n"
    )
    (tmp_path / "model_parameters.yaml").write_text(
        "parameters:\n"
        "  capacidade_max:\n"
        "    index: [PERIODOS]\n"
        "    source: data.capacidade\n"
        "    mutable: true\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path), periodos=[1, 2], capacidade={1: 100, 2: 200}
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Parameters().attach_to_model(model, data)

    assert model.capacidade_max.mutable
