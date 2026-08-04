from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.constraints.orchestrator import Constraints


def test_attach_to_model_calls_enabled_rule(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "constraints:\n"
        "  capacidade:\n"
        "    enabled: true\n"
        "    rule: tests.constraints.fixtures.MarkerRule\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Constraints().attach_to_model(model, data)

    assert hasattr(model, "marker_called")


def test_attach_to_model_skips_disabled_rule(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "constraints:\n"
        "  capacidade:\n"
        "    enabled: false\n"
        "    rule: tests.constraints.fixtures.MarkerRule\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Constraints().attach_to_model(model, data)

    assert not hasattr(model, "marker_called")


def test_attach_to_model_defaults_enabled_to_true(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "constraints:\n  capacidade:\n    rule: tests.constraints.fixtures.MarkerRule\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Constraints().attach_to_model(model, data)

    assert hasattr(model, "marker_called")


def test_attach_to_model_invalid_module_raises(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "constraints:\n  capacidade:\n    rule: nonexistent.module.Rule\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    with pytest.raises(ModuleNotFoundError):
        Constraints().attach_to_model(model, data)


def test_attach_to_model_rule_builds_real_constraint(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "constraints:\n  limite:\n    rule: tests.constraints.fixtures.SumConstraintRule\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)

    Constraints().attach_to_model(model, data)

    assert isinstance(model.limite, pyo.Constraint)
