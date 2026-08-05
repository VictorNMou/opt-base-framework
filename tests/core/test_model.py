from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.core.model import Model
from optframework.core.validation import ConfigValidationError


def _write_valid_config(tmp_path: Path) -> None:
    # pylint: disable=duplicate-code
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.produtos\n"
    )
    (tmp_path / "model_parameters.yaml").write_text(
        "parameters:\n  capacidade_max:\n    source: data.capacidade\n"
    )
    (tmp_path / "model_variables.yaml").write_text(
        "variables:\n  producao:\n    index: [PRODUTOS]\n    domain: NonNegativeReals\n"
    )
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.strategy.fixtures.FakeRules\n"
        "constraints:\n  capacidade: {}\n"
    )
    (tmp_path / "model_objective.yaml").write_text(
        "rules_class: tests.strategy.fixtures.FakeObjectives\n"
        "default: maximizar\n"
        "objectives:\n  maximizar:\n    sense: maximize\n"
    )


def test_build_valid_config_attaches_all_artifacts(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    data = SimpleNamespace(
        config_dir=str(tmp_path), produtos=["p1", "p2"], capacidade=10.0
    )

    model = Model(data).build()

    assert isinstance(model, pyo.ConcreteModel)
    assert list(model.PRODUTOS) == ["p1", "p2"]
    assert model.maximizar.active


def test_build_invalid_config_raises_before_attaching_anything(tmp_path: Path) -> None:
    _write_valid_config(tmp_path)
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n  PRODUTOS:\n    source: data.inexistente\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path), produtos=["p1", "p2"], capacidade=10.0
    )
    instance = Model(data)

    with pytest.raises(ConfigValidationError):
        instance.build()

    assert not hasattr(instance.model, "PRODUTOS")
