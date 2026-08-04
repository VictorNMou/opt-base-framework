from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo

from optframework.solver.pyomo_adapter import PyomoAdapter
from optframework.solver.scenario import ScenarioLoop


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=[1, 2])
    model.capacidade = pyo.Param(model.I, initialize={1: 10, 2: 10}, mutable=True)
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.limite = pyo.Constraint(
        expr=model.x[1] + model.x[2] <= model.capacidade[1] + model.capacidade[2]
    )
    model.obj = pyo.Objective(expr=model.x[1] + model.x[2], sense=pyo.maximize)
    return model


def test_missing_config_file_runs_single_solve(tmp_path: Path) -> None:
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    result = ScenarioLoop().run(model, data, PyomoAdapter())

    assert result.termination_condition == pyo.TerminationCondition.optimal


def test_disabled_runs_single_solve(tmp_path: Path) -> None:
    (tmp_path / "model_scenarios.yaml").write_text("enabled: false\n")
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    result = ScenarioLoop().run(model, data, PyomoAdapter())

    assert result.termination_condition == pyo.TerminationCondition.optimal


def test_enabled_runs_loop_with_different_results(tmp_path: Path) -> None:
    (tmp_path / "model_scenarios.yaml").write_text(
        "enabled: true\n"
        "profile: default\n"
        "scenarios:\n"
        "  - name: baixa\n"
        "    param_overrides:\n"
        "      capacidade: {1: 5, 2: 5}\n"
        "  - name: alta\n"
        "    param_overrides:\n"
        "      capacidade: {1: 50, 2: 50}\n"
    )
    data = SimpleNamespace(config_dir=str(tmp_path))
    model = _new_model()

    results = ScenarioLoop().run(model, data, PyomoAdapter())

    assert set(results.keys()) == {"baixa", "alta"}
    assert sum(results["alta"].values.values()) > sum(results["baixa"].values.values())
