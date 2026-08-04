import pyomo.environ as pyo

from optframework.results.result import Result
from optframework.solver.scenario import Scenario, ScenarioRunner


class _FakeSolver:
    """Solver fake: registra os perfis/labels usados, sem resolver de verdade."""

    def __init__(self) -> None:
        self.profiles_used: list[str] = []
        self.labels_used: list[str | None] = []

    def solve(
        self,
        model: pyo.ConcreteModel,
        profile: str = "default",
        label: str | None = None,
        data: object | None = None,
    ) -> Result:
        self.profiles_used.append(profile)
        self.labels_used.append(label)
        return Result(termination_condition="fake", values={})

    def get_results(self) -> Result:
        return Result(termination_condition="fake", values={})


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=[1, 2])
    model.capacidade = pyo.Param(model.I, initialize={1: 100, 2: 100}, mutable=True)
    model.x = pyo.Var(model.I, domain=pyo.NonNegativeReals)
    model.limite = pyo.Constraint(expr=model.x[1] + model.x[2] <= model.capacidade[1])
    model.obj_min = pyo.Objective(expr=model.x[1], sense=pyo.minimize)
    model.obj_max = pyo.Objective(expr=model.x[2], sense=pyo.maximize)
    model.obj_max.deactivate()
    return model


def test_param_override_applied_per_index() -> None:
    model = _new_model()
    scenario = Scenario(name="c1", param_overrides={"capacidade": {1: 250, 2: 300}})

    ScenarioRunner(model, _FakeSolver()).run([scenario])

    assert pyo.value(model.capacidade[1]) == 250
    assert pyo.value(model.capacidade[2]) == 300


def test_param_override_applied_as_scalar() -> None:
    model = _new_model()
    model.fator = pyo.Param(initialize=1.0, mutable=True)
    scenario = Scenario(name="c1", param_overrides={"fator": 2.5})

    ScenarioRunner(model, _FakeSolver()).run([scenario])

    assert pyo.value(model.fator) == 2.5


def test_fixed_variables_fixes_scalar_value() -> None:
    model = _new_model()
    model.folga = pyo.Var(domain=pyo.NonNegativeReals)
    scenario = Scenario(name="c1", fixed_variables={"folga": 3.0})

    ScenarioRunner(model, _FakeSolver()).run([scenario])

    assert model.folga.fixed
    assert pyo.value(model.folga) == 3.0


def test_active_constraints_toggle() -> None:
    model = _new_model()
    scenario = Scenario(name="c1", active_constraints={"limite": False})

    ScenarioRunner(model, _FakeSolver()).run([scenario])

    assert not model.limite.active


def test_active_objective_switches_without_rebuild() -> None:
    model = _new_model()
    scenario = Scenario(name="c1", active_objective="obj_max")

    ScenarioRunner(model, _FakeSolver()).run([scenario])

    assert model.obj_max.active
    assert not model.obj_min.active


def test_fixed_variables_fixes_value() -> None:
    model = _new_model()
    scenario = Scenario(name="c1", fixed_variables={"x": {1: 5.0}})

    ScenarioRunner(model, _FakeSolver()).run([scenario])

    assert model.x[1].fixed
    assert pyo.value(model.x[1]) == 5.0


def test_solver_profile_override_per_scenario() -> None:
    model = _new_model()
    solver = _FakeSolver()
    scenario = Scenario(name="c1", solver_profile="optimal")

    ScenarioRunner(model, solver).run([scenario], profile="default")

    assert solver.profiles_used == ["optimal"]


def test_run_returns_result_per_scenario_name() -> None:
    model = _new_model()
    scenarios = [Scenario(name="a"), Scenario(name="b")]

    results = ScenarioRunner(model, _FakeSolver()).run(scenarios)

    assert set(results.keys()) == {"a", "b"}


def test_run_passes_scenario_name_as_label() -> None:
    model = _new_model()
    solver = _FakeSolver()
    scenarios = [Scenario(name="a"), Scenario(name="b")]

    ScenarioRunner(model, solver).run(scenarios)

    assert solver.labels_used == ["a", "b"]
