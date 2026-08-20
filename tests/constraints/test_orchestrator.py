from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.constraints.orchestrator import Constraints


def test_attach_to_model_calls_enabled_rule(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n"
        "  marker:\n"
        "    enabled: true\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Constraints().attach_to_model(model, data)

    assert hasattr(model, "marker")


def test_attach_to_model_does_not_apply_enabled(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n"
        "  marker:\n"
        "    enabled: false\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Constraints().attach_to_model(model, data)

    assert hasattr(model, "marker")
    assert model.marker.active


def test_apply_enabled_static_false_deactivates_rule(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n"
        "  marker:\n"
        "    enabled: false\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    constraints = Constraints()
    constraints.attach_to_model(model, data)

    constraints.apply_enabled(model, data)

    assert not model.marker.active


def test_apply_enabled_static_true_keeps_rule_active(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n"
        "  marker:\n"
        "    enabled: true\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    constraints = Constraints()
    constraints.attach_to_model(model, data)

    constraints.apply_enabled(model, data)

    assert model.marker.active


def test_attach_to_model_defaults_enabled_to_true(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  marker: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    Constraints().attach_to_model(model, data)

    assert hasattr(model, "marker")


def test_attach_to_model_invalid_module_raises(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: nonexistent.module.Rules\nconstraints:\n  marker: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()

    with pytest.raises(ModuleNotFoundError):
        Constraints().attach_to_model(model, data)


def test_attach_to_model_rule_builds_real_constraint(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  limite: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)

    Constraints().attach_to_model(model, data)

    assert isinstance(model.limite, pyo.Constraint)


def test_apply_enabled_defaults_missing_enabled_to_true(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  marker: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    constraints = Constraints()
    constraints.attach_to_model(model, data)
    model.marker.deactivate()

    constraints.apply_enabled(model, data)

    assert model.marker.active


def test_set_enabled_deactivates_by_name(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  marker: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    constraints = Constraints()
    constraints.attach_to_model(model, data)

    constraints.set_enabled(model, {"marker": False})

    assert not model.marker.active


def test_set_enabled_reactivates_by_name(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  marker: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    constraints = Constraints()
    constraints.attach_to_model(model, data)
    model.marker.deactivate()

    constraints.set_enabled(model, {"marker": True})

    assert model.marker.active


def test_set_enabled_does_not_touch_families_absent_from_the_dict(
    tmp_path: Path,
) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  marker: {}\n  limite: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    constraints = Constraints()
    constraints.attach_to_model(model, data)

    constraints.set_enabled(model, {"marker": False})

    assert not model.marker.active
    assert model.limite.active


def test_set_enabled_unknown_name_raises_key_error(tmp_path: Path) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n  marker: {}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    constraints = Constraints()
    constraints.attach_to_model(model, data)

    with pytest.raises(KeyError, match="inexistente"):
        constraints.set_enabled(model, {"inexistente": False})


def test_attach_to_model_indexed_constraint_builds_one_per_index(
    tmp_path: Path,
) -> None:
    (tmp_path / "model_constraints.yaml").write_text(
        "rules_class: tests.constraints.fixtures.FakeRules\n"
        "constraints:\n"
        "  limite_por_item:\n"
        "    index: [ITEMS]\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = pyo.ConcreteModel()
    model.ITEMS = pyo.Set(initialize=["a", "b"])
    model.y = pyo.Var(model.ITEMS, domain=pyo.NonNegativeReals)

    Constraints().attach_to_model(model, data)

    assert isinstance(model.limite_por_item, pyo.Constraint)
    assert set(model.limite_por_item.keys()) == {"a", "b"}
