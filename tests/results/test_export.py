import json
from pathlib import Path

import pyomo.environ as pyo
import pytest

from optframework.results.export import result_to_dict, write_result_json
from optframework.results.infeasibility import ConstraintViolation, InfeasibilityReport
from optframework.results.metrics import SolveMetrics
from optframework.results.result import Result
from optframework.results.sensitivity import ConstraintDual, SensitivityReport
from optframework.solver.pyomo_adapter import PyomoAdapter


def _full_result() -> Result:
    return Result(
        termination_condition=pyo.TerminationCondition.optimal,
        values={("x", None): 5.0},
        infeasibility=InfeasibilityReport(
            method="elastic_relaxation",
            violations=[ConstraintViolation("c1", None, "upper", 2.0)],
        ),
        metrics=SolveMetrics(
            wall_time_seconds=0.01, lower_bound=5.0, upper_bound=5.0, gap=0.0
        ),
        sensitivity=SensitivityReport(duals=[ConstraintDual("c1", None, 3.0)]),
    )


def test_result_to_dict_round_trips_via_json_loads_dumps() -> None:
    data = result_to_dict(_full_result(), solution={"x": 5.0})

    round_tripped = json.loads(json.dumps(data))

    assert round_tripped["termination_condition"] == "optimal"
    assert round_tripped["solution"] == {"x": 5.0}
    assert round_tripped["metrics"]["wall_time_seconds"] == pytest.approx(0.01)
    assert round_tripped["infeasibility"]["method"] == "elastic_relaxation"
    assert round_tripped["sensitivity"]["duals"][0]["dual"] == pytest.approx(3.0)


def test_multidimensional_indexed_variable_keys_are_stringified() -> None:
    model = pyo.ConcreteModel()
    model.IJ = pyo.Set(dimen=2, initialize=[("a", 1), ("b", 2)])
    model.x = pyo.Var(model.IJ, domain=pyo.NonNegativeReals, bounds=(0, 5))
    model.obj = pyo.Objective(
        expr=sum(model.x[k] for k in model.IJ), sense=pyo.maximize
    )

    result = PyomoAdapter().solve(model)
    solution = {"x": {index: value for (_, index), value in result.values.items()}}

    data = result_to_dict(result, solution)

    assert set(data["solution"]["x"].keys()) == {"('a', 1)", "('b', 2)"}
    # não deveria explodir: tudo aqui já é str/int/float/bool/None
    json.dumps(data)


def test_write_result_json_creates_file_and_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "result.json"

    path = write_result_json(_full_result(), {"x": 5.0}, target)

    assert path == target
    assert path.exists()
    assert json.loads(path.read_text()) == result_to_dict(_full_result(), {"x": 5.0})


def test_export_with_none_infeasibility_and_sensitivity() -> None:
    result = Result(
        termination_condition=pyo.TerminationCondition.optimal,
        values={},
        metrics=SolveMetrics(wall_time_seconds=0.01),
    )

    data = result_to_dict(result, solution={})

    assert data["infeasibility"] is None
    assert data["sensitivity"] is None
    assert "infeasibility" in data
    assert "sensitivity" in data


def test_termination_condition_serializes_as_plain_string() -> None:
    result = Result(
        termination_condition=pyo.TerminationCondition.infeasible, values={}
    )

    data = result_to_dict(result, solution={})

    assert data["termination_condition"] == "infeasible"
    assert data["is_infeasible"] is True
