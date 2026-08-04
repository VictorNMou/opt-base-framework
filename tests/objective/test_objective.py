from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.objective.objective import Objective
from tests.objective.fixtures import CountingRule


def _write_config(tmp_path: Path) -> None:
    (tmp_path / "model_objective.yaml").write_text(
        "default: minimizar\n"
        "objectives:\n"
        "  minimizar:\n"
        "    sense: minimize\n"
        "    rule: tests.objective.fixtures.CountingRule\n"
        "  maximizar:\n"
        "    sense: maximize\n"
        "    rule: tests.objective.fixtures.OtherRule\n"
    )


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var()
    model.y = pyo.Var()
    return model


def test_attach_to_model_uses_default_profile(tmp_path: Path) -> None:
    CountingRule.call_count = 0
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    Objective().attach_to_model(model, data)

    assert model.minimizar.active
    assert not model.maximizar.active
    assert model.minimizar.sense == pyo.minimize


def test_attach_to_model_explicit_profile_switches_active(tmp_path: Path) -> None:
    CountingRule.call_count = 0
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    Objective().attach_to_model(model, data)

    Objective().attach_to_model(model, data, profile="maximizar")

    assert model.maximizar.active
    assert not model.minimizar.active
    assert model.maximizar.sense == pyo.maximize


def test_switching_profile_does_not_rebuild_existing_objective(tmp_path: Path) -> None:
    CountingRule.call_count = 0
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    Objective().attach_to_model(model, data)
    assert CountingRule.call_count == 1

    Objective().attach_to_model(model, data, profile="maximizar")
    Objective().attach_to_model(model, data, profile="minimizar")

    assert CountingRule.call_count == 1


def test_overwrite_forces_rebuild(tmp_path: Path) -> None:
    CountingRule.call_count = 0
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    Objective().attach_to_model(model, data)
    assert CountingRule.call_count == 1

    Objective().attach_to_model(model, data, overwrite=True)

    assert CountingRule.call_count == 2


def test_unknown_profile_raises(tmp_path: Path) -> None:
    CountingRule.call_count = 0
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    with pytest.raises(KeyError):
        Objective().attach_to_model(model, data, profile="inexistente")
