import pyomo.environ as pyo
import pytest

from optframework.solver.infeasibility.elastic import ElasticRelaxationAnalyzer


def _analyzer(**kwargs) -> ElasticRelaxationAnalyzer:
    return ElasticRelaxationAnalyzer(solver_name="appsi_highs", **kwargs)


def test_equality_violation_detected() -> None:
    # bounds=(5, 5) trava x=5 no domínio (não elasticizável); só c_eq pode ser relaxada.
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.Reals, bounds=(5, 5))
    model.c_eq = pyo.Constraint(expr=model.x == 12)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    assert report.method == "elastic_relaxation"
    assert not report.suspected_bound_conflict
    assert len(report.violations) == 1
    violation = report.violations[0]
    assert violation.constraint_name == "c_eq"
    assert violation.side == "eq"
    assert violation.slack == pytest.approx(7.0)


def test_lower_bound_violation_detected() -> None:
    # bounds=(None, 5) trava x<=5 no domínio (não elasticizável); só c_lower pode ser relaxada.
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(None, 5))
    model.c_lower = pyo.Constraint(expr=model.x >= 10)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    assert len(report.violations) == 1
    assert report.violations[0].constraint_name == "c_lower"
    assert report.violations[0].side == "lower"
    assert report.violations[0].slack == pytest.approx(5.0)


def test_upper_bound_violation_detected() -> None:
    # bounds=(10, None) trava x>=10 no domínio (não elasticizável); só c_upper pode ser relaxada.
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(10, None))
    model.c_upper = pyo.Constraint(expr=model.x <= 5)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    assert len(report.violations) == 1
    assert report.violations[0].constraint_name == "c_upper"
    assert report.violations[0].side == "upper"
    assert report.violations[0].slack == pytest.approx(5.0)


def test_ranged_constraint_violation_detected() -> None:
    # bounds=(5, 5) trava x=5 no domínio (não elasticizável); só c_ranged pode ser relaxada.
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(5, 5))
    model.c_ranged = pyo.Constraint(expr=(20, model.x, 30))
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    assert len(report.violations) == 1
    violation = report.violations[0]
    assert violation.constraint_name == "c_ranged"
    assert violation.side == "lower"
    assert violation.slack == pytest.approx(15.0)


def test_violation_below_tolerance_excluded() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_lower = pyo.Constraint(expr=model.x >= 10)
    model.c_cap = pyo.Constraint(expr=model.x <= 9.5)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer(tolerance=1.0).analyze(model)

    assert report.violations == []
    assert not report.suspected_bound_conflict
    assert "inconclusivo" in report.render()


def test_bound_conflict_detected_when_no_constraint_helps() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(bounds=(10, 5))
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    assert report.suspected_bound_conflict
    assert report.violations == []


def test_multiple_violations_sorted_by_slack_descending() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.y = pyo.Var(domain=pyo.NonNegativeReals)
    model.c_x = pyo.Constraint(expr=model.x >= 20)
    model.c_y = pyo.Constraint(expr=model.y >= 5)
    model.c_cap = pyo.Constraint(expr=model.x + model.y <= 1)
    model.obj = pyo.Objective(expr=model.x + model.y, sense=pyo.minimize)

    report = _analyzer().analyze(model)

    slacks = [v.slack for v in report.violations]
    assert slacks == sorted(slacks, reverse=True)
    assert len(report.violations) == 2


def test_component_name_collision_raises() -> None:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.infeasibility_slacks = pyo.VarList(domain=pyo.NonNegativeReals)
    model.c = pyo.Constraint(expr=model.x >= 1)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)

    with pytest.raises(ValueError, match="infeasibility_slacks"):
        _analyzer().analyze(model)
