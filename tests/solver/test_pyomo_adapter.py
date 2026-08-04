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
    assert result.values["y"] == pytest.approx(10.0)
    assert result.values["x"] == pytest.approx(0.0)


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
