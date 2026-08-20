from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.objective.objective import Objective
from tests.objective.fixtures import FakeObjectives


def _write_config(tmp_path: Path) -> None:
    (tmp_path / "model_objective.yaml").write_text(
        "rules_class: tests.objective.fixtures.FakeObjectives\n"
        "default: minimizar\n"
        "objectives:\n"
        "  minimizar:\n"
        "    sense: minimize\n"
        "  maximizar:\n"
        "    sense: maximize\n"
    )


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var()
    model.y = pyo.Var()
    return model


def test_attach_to_model_attaches_all_objectives(tmp_path: Path) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    Objective().attach_to_model(model, data)

    assert hasattr(model, "minimizar")
    assert hasattr(model, "maximizar")
    assert model.minimizar.sense == pyo.minimize
    assert model.maximizar.sense == pyo.maximize


def test_attach_to_model_does_not_apply_profile(tmp_path: Path) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    Objective().attach_to_model(model, data)

    assert model.minimizar.active
    assert model.maximizar.active


def test_overwrite_forces_rebuild(tmp_path: Path) -> None:
    FakeObjectives.call_count = 0
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    Objective().attach_to_model(model, data)
    assert FakeObjectives.call_count == 1

    Objective().attach_to_model(model, data, overwrite=True)

    assert FakeObjectives.call_count == 2


def test_apply_profile_uses_default_from_config(tmp_path: Path) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    objective = Objective()
    objective.attach_to_model(model, data)

    objective.apply_profile(model, data)

    assert model.minimizar.active
    assert not model.maximizar.active


def test_apply_profile_explicit_profile_switches_active(tmp_path: Path) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    objective = Objective()
    objective.attach_to_model(model, data)
    objective.apply_profile(model, data)

    objective.apply_profile(model, data, profile="maximizar")

    assert model.maximizar.active
    assert not model.minimizar.active


def test_apply_profile_unknown_profile_raises(tmp_path: Path) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    objective = Objective()
    objective.attach_to_model(model, data)

    with pytest.raises(KeyError):
        objective.apply_profile(model, data, profile="inexistente")


def test_set_active_activates_by_name_and_deactivates_the_rest(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    objective = Objective()
    objective.attach_to_model(model, data)

    objective.set_active(model, "maximizar")

    assert model.maximizar.active
    assert not model.minimizar.active


def test_set_active_unknown_name_raises_key_error_without_deactivating(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()
    objective = Objective()
    objective.attach_to_model(model, data)

    with pytest.raises(KeyError, match="inexistente"):
        objective.set_active(model, "inexistente")

    assert model.minimizar.active
    assert model.maximizar.active
