from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.solver.metrics import _safe_bound, build_solve_metrics
from optframework.solver.pyomo_adapter import PyomoAdapter


def _raw_results(lower_bound: float | None, upper_bound: float | None) -> SimpleNamespace:
    return SimpleNamespace(problem=SimpleNamespace(lower_bound=lower_bound, upper_bound=upper_bound))


def test_wall_time_is_positive_after_real_solve() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c = pyo.Constraint(expr=model.x <= 5)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.maximize)

    result = PyomoAdapter().solve(model)

    assert result.metrics is not None
    assert result.metrics.wall_time_seconds > 0


def test_gap_computed_from_plain_floats() -> None:
    metrics = build_solve_metrics(_raw_results(90.0, 100.0), wall_time_seconds=1.0)

    assert metrics.lower_bound == pytest.approx(90.0)
    assert metrics.upper_bound == pytest.approx(100.0)
    assert metrics.gap == pytest.approx(0.1)


def test_bounds_none_on_infeasible_solve() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c1 = pyo.Constraint(expr=model.x >= 10)
    model.c2 = pyo.Constraint(expr=model.x <= 5)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    result = PyomoAdapter().solve(model)

    assert result.metrics is not None
    assert result.metrics.lower_bound is None
    assert result.metrics.upper_bound is None
    assert result.metrics.gap is None


def test_bounds_populated_on_feasible_lp() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c = pyo.Constraint(expr=model.x <= 5)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.maximize)

    result = PyomoAdapter().solve(model)

    assert result.metrics.lower_bound == pytest.approx(5.0)
    assert result.metrics.upper_bound == pytest.approx(5.0)
    assert result.metrics.gap == pytest.approx(0.0)


def test_bounds_populated_on_feasible_milp() -> None:
    # pylint: disable=duplicate-code
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=["A", "B", "C"])
    model.x = pyo.Var(model.I, domain=pyo.Binary)
    model.peso = pyo.Param(model.I, initialize={"A": 10, "B": 20, "C": 30})
    model.valor = pyo.Param(model.I, initialize={"A": 60, "B": 100, "C": 120})
    model.cap = pyo.Constraint(
        expr=sum(model.peso[i] * model.x[i] for i in model.I) <= 50
    )
    model.obj = pyo.Objective(
        expr=sum(model.valor[i] * model.x[i] for i in model.I), sense=pyo.maximize
    )

    result = PyomoAdapter().solve(model)

    assert result.metrics.lower_bound == pytest.approx(220.0)
    assert result.metrics.upper_bound == pytest.approx(220.0)
    assert result.metrics.gap == pytest.approx(0.0)


def test_safe_bound_treats_infinite_as_unavailable() -> None:
    assert _safe_bound(float("inf")) is None
    assert _safe_bound(float("-inf")) is None
    assert _safe_bound(None) is None
    assert _safe_bound(5.0) == pytest.approx(5.0)
