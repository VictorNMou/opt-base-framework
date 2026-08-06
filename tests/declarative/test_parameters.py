from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

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


def test_attach_to_model_uses_default_for_missing_index_values(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n"
    )
    (tmp_path / "model_parameters.yaml").write_text(
        "parameters:\n"
        "  desconto:\n"
        "    index: [PRODUTOS]\n"
        "    source: data.desconto\n"
        "    default: 0.0\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path),
        produtos=["p1", "p2", "p3"],
        desconto={"p1": 0.1},
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Parameters().attach_to_model(model, data)

    assert model.desconto["p1"] == 0.1
    assert model.desconto["p2"] == 0.0
    assert model.desconto["p3"] == 0.0


def test_attach_to_model_without_default_raises_on_missing_index_value(
    tmp_path: Path,
) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n"
    )
    (tmp_path / "model_parameters.yaml").write_text(
        "parameters:\n"
        "  desconto:\n"
        "    index: [PRODUTOS]\n"
        "    source: data.desconto\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path),
        produtos=["p1", "p2"],
        desconto={"p1": 0.1},
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Parameters().attach_to_model(model, data)

    with pytest.raises(ValueError, match="no default value is specified"):
        _ = model.desconto["p2"]


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


def test_attach_to_model_within_restricts_to_custom_set(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n  VALIDOS:\n    source: data.validos\n"
    )
    (tmp_path / "model_parameters.yaml").write_text(
        "parameters:\n"
        "  substituto:\n"
        "    index: [PRODUTOS]\n"
        "    source: data.substituto\n"
        "    within: VALIDOS\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path),
        produtos=["p1", "p2"],
        validos=["p1", "p2"],
        substituto={"p1": "p2", "p2": "p1"},
    )
    model = pyo.ConcreteModel()
    Sets().attach_to_model(model, data)

    Parameters().attach_to_model(model, data)

    assert model.substituto.domain is model.VALIDOS
    assert model.substituto.extract_values() == {"p1": "p2", "p2": "p1"}
