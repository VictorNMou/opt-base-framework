from pathlib import Path

import pyomo.environ as pyo
import pytest

from optframework.solver.pyomo_adapter import PyomoAdapter


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.y = pyo.Var(domain=pyo.NonNegativeReals)
    model.limite = pyo.Constraint(expr=model.x + model.y <= 10)
    model.obj = pyo.Objective(expr=model.x + 2 * model.y, sense=pyo.maximize)
    return model


def test_solve_returns_optimal_result() -> None:
    model = _new_model()

    result = PyomoAdapter().solve(model)

    assert result.termination_condition == pyo.TerminationCondition.optimal
    assert result.values[("y", None)] == pytest.approx(10.0)
    assert result.values[("x", None)] == pytest.approx(0.0)
    assert result.is_infeasible is False
    assert result.infeasibility is None


def test_solve_indexed_var_uses_native_name_index_key() -> None:
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=["p1", "p2"])
    model.producao = pyo.Var(model.I, domain=pyo.NonNegativeReals, bounds=(0, 5))
    model.obj = pyo.Objective(
        expr=sum(model.producao[i] for i in model.I), sense=pyo.maximize
    )

    result = PyomoAdapter().solve(model)

    assert result.values[("producao", "p1")] == pytest.approx(5.0)
    assert result.values[("producao", "p2")] == pytest.approx(5.0)


def test_solve_unknown_profile_raises() -> None:
    model = _new_model()

    with pytest.raises(KeyError):
        PyomoAdapter().solve(model, profile="inexistente")


def test_get_results_before_solve_raises() -> None:
    with pytest.raises(ValueError, match="Nenhum solve"):
        PyomoAdapter().get_results()


def test_get_results_after_solve_returns_same_result() -> None:
    model = _new_model()
    adapter = PyomoAdapter()

    result = adapter.solve(model)

    assert adapter.get_results() is result


def test_report_enabled_writes_before_and_after_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    (tmp_path / "model_solver.yaml").write_text(
        f"report:\n  enabled: true\n  output_dir: {output_dir}\n"
        "profiles:\n  default:\n    solver_name: appsi_highs\n    tee: false\n    options: {}\n"
    )
    model = _new_model()

    PyomoAdapter(config_dir=tmp_path).solve(model, label="cenario_x")

    assert (output_dir / "pprint_before_cenario_x.txt").exists()
    assert (output_dir / "display_after_cenario_x.txt").exists()


def test_report_disabled_writes_no_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    (tmp_path / "model_solver.yaml").write_text(
        "profiles:\n  default:\n    solver_name: appsi_highs\n    tee: false\n    options: {}\n"
    )
    model = _new_model()

    PyomoAdapter(config_dir=tmp_path).solve(model)

    assert not output_dir.exists()


def _infeasible_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_lower = pyo.Constraint(expr=model.x >= 10)
    model.c_upper = pyo.Constraint(expr=model.x <= 5)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)
    return model


def test_infeasible_solve_does_not_raise_and_reports_infeasibility() -> None:
    model = _infeasible_model()

    result = PyomoAdapter().solve(model)

    assert result.termination_condition == pyo.TerminationCondition.infeasible
    assert result.is_infeasible is True
    assert result.values == {}
    assert result.infeasibility is not None
    assert result.infeasibility.method == "elastic_relaxation"
    assert len(result.infeasibility.violations) > 0


def test_infeasibility_disabled_via_config(tmp_path: Path) -> None:
    (tmp_path / "model_solver.yaml").write_text(
        "profiles:\n  default:\n    solver_name: appsi_highs\n    tee: false\n    options: {}\n"
        "infeasibility:\n  enabled: false\n"
    )
    model = _infeasible_model()

    result = PyomoAdapter(config_dir=tmp_path).solve(model)

    assert result.is_infeasible is True
    assert result.infeasibility is None


def test_infeasible_solve_with_report_enabled_writes_infeasibility_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    (tmp_path / "model_solver.yaml").write_text(
        f"report:\n  enabled: true\n  output_dir: {output_dir}\n"
        "profiles:\n  default:\n    solver_name: appsi_highs\n    tee: false\n    options: {}\n"
    )
    model = _infeasible_model()

    PyomoAdapter(config_dir=tmp_path).solve(model, label="cenario_x")

    infeasibility_path = output_dir / "infeasibility_cenario_x.txt"
    assert infeasibility_path.exists()
    assert "c_" in infeasibility_path.read_text()
