from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.results.result import Result
from optframework.strategy.milp_strategy import MilpStrategy


def test_extract_solution_groups_indexed_var_by_name() -> None:
    result = Result(
        termination_condition="optimal",
        values={
            ("producao", ("p1", 1)): 10.0,
            ("producao", ("p2", 2)): 5.0,
            ("folga", None): 3.0,
        },
    )

    solution = MilpStrategy().extract_solution(result)

    assert solution == {
        "producao": {("p1", 1): 10.0, ("p2", 2): 5.0},
        "folga": 3.0,
    }


def test_extract_solution_empty_values_returns_empty_dict() -> None:
    result = Result(termination_condition="optimal", values={})

    solution = MilpStrategy().extract_solution(result)

    assert solution == {}


def test_build_model_solve_extract_solution_end_to_end(tmp_path: Path) -> None:
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
    data = SimpleNamespace(
        config_dir=str(tmp_path), produtos=["p1", "p2"], capacidade=10.0
    )
    strategy = MilpStrategy()

    model = strategy.build_model(data)
    result = strategy.solve(model)
    solution = strategy.extract_solution(result)

    assert result.termination_condition == pyo.TerminationCondition.optimal
    assert sum(solution["producao"].values()) == pytest.approx(10.0)
