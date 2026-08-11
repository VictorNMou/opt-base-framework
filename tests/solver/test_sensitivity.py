import pyomo.environ as pyo
import pytest

from optframework.solver import sensitivity as sensitivity_module
from optframework.solver.sensitivity import SensitivityAnalyzer
from tests.solver.fixtures import CyIpoptLikeSolver


def _analyzer(**kwargs) -> SensitivityAnalyzer:
    return SensitivityAnalyzer(solver_name="appsi_highs", **kwargs)


def _mixed_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.b = pyo.Var(domain=pyo.Binary)
    model.c1 = pyo.Constraint(expr=model.x + 5 * model.b <= 10)
    model.obj = pyo.Objective(expr=3 * model.x + 2 * model.b, sense=pyo.maximize)
    return model


def _solve(model: pyo.ConcreteModel) -> None:
    opt = pyo.SolverFactory("appsi_highs")
    raw = opt.solve(model, load_solutions=False, symbolic_solver_labels=True)
    model.solutions.load_from(raw)


def test_dual_on_mixed_continuous_binary_model_is_meaningful() -> None:
    model = _mixed_model()
    _solve(model)

    report = _analyzer().analyze(model)

    assert report.resolved
    assert report.fixed_variable_count == 1
    duals = {d.constraint_name: d.dual for d in report.duals}
    assert duals["c1"] == pytest.approx(3.0)


def test_reduced_cost_is_none_or_float_never_raises() -> None:
    model = _mixed_model()
    _solve(model)

    report = _analyzer().analyze(model)

    assert len(report.reduced_costs) == 1
    assert report.reduced_costs[0].var_name == "x"
    assert report.reduced_costs[0].reduced_cost is None or isinstance(
        report.reduced_costs[0].reduced_cost, float
    )


def test_raw_dual_suffix_raises_on_unfixed_integer_model() -> None:
    model = _mixed_model()
    _solve(model)
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    opt = pyo.SolverFactory("appsi_highs")
    with pytest.raises(RuntimeError, match="valid duals"):
        opt.solve(model, load_solutions=False, symbolic_solver_labels=True)


def test_analyzer_does_not_raise_on_same_model_that_crashes_raw_suffix() -> None:
    model = _mixed_model()
    _solve(model)

    report = _analyzer().analyze(model)

    assert report.resolved


def test_all_binary_model_gives_zero_duals_not_error() -> None:
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
    _solve(model)

    report = _analyzer().analyze(model)

    assert report.resolved
    assert report.fixed_variable_count == 3
    assert all(d.dual == pytest.approx(0.0) for d in report.duals)
    assert "esperado, não um erro" in report.render()


def test_fixed_variable_count_matches_non_continuous_vars() -> None:
    model = _mixed_model()
    _solve(model)

    report = _analyzer().analyze(model)

    assert report.fixed_variable_count == 1


def test_unresolved_fixed_solve_returns_resolved_false() -> None:
    model = pyo.ConcreteModel()
    model.b = pyo.Var(domain=pyo.Binary)
    model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 0))
    # x preso em 0; força infeasibilidade só quando b=1, mas o solve original escolhe b=0.
    # Para exercitar resolved=False, fixamos manualmente um cenário contraditório após "resolver".
    model.b.fix(1)
    model.c = pyo.Constraint(expr=model.x >= 1)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    assert report.resolved is False
    assert "não convergiu" in report.render()


def test_analyze_survives_solver_without_options_attribute_and_strict_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reproduz o solver_name="cyipopt" (PyomoCyIpoptSolver): sem `.options`, rejeita
    # `symbolic_solver_labels` — antes do fix, `opt.options.update(...)` já crashava com
    # AttributeError antes de sequer tentar resolver.
    stub = CyIpoptLikeSolver()
    monkeypatch.setattr(sensitivity_module.pyo, "SolverFactory", lambda _name: stub)
    model = pyo.ConcreteModel()
    model.b = pyo.Var(domain=pyo.Binary)
    model.b.set_value(1)
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c = pyo.Constraint(expr=model.x + model.b <= 10)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = SensitivityAnalyzer(solver_name="cyipopt").analyze(model)

    assert report.resolved is False
    assert report.fixed_variable_count == 1
    assert stub.calls[-1] == {"load_solutions": False, "options": {}}
