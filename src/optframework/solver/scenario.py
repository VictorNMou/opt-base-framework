from dataclasses import dataclass, field
from typing import Any

import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder
from optframework.results.result import Result
from optframework.solver.adapter import SolverAdapter


@dataclass
class Scenario:
    """Descreve as mutações a aplicar no modelo já construído antes de resolver."""

    name: str
    param_overrides: dict[str, Any] = field(default_factory=dict)
    active_objective: str | None = None
    active_constraints: dict[str, bool] = field(default_factory=dict)
    fixed_variables: dict[str, Any] = field(default_factory=dict)
    solver_profile: str | None = None


class ScenarioRunner:
    """Resolve múltiplas instâncias do mesmo modelo já montado, sem reconstruí-lo."""

    def __init__(self, model: pyo.ConcreteModel, solver: SolverAdapter) -> None:
        """Guarda o modelo já construído e o adapter de solver a usar em cada cenário."""
        self.model = model
        self.solver = solver

    def run(self, scenarios: list[Scenario], profile: str = "default") -> dict[str, Result]:
        """Aplica cada cenário e resolve, devolvendo o Result por nome de cenário."""
        results: dict[str, Result] = {}
        for scenario in scenarios:
            self._apply(scenario)
            chosen_profile = scenario.solver_profile or profile
            results[scenario.name] = self.solver.solve(
                self.model, profile=chosen_profile, label=scenario.name
            )
        return results

    def _apply(self, scenario: Scenario) -> None:
        for name, value in scenario.param_overrides.items():
            self._set_param(name, value)
        for name, active in scenario.active_constraints.items():
            component = getattr(self.model, name)
            component.activate() if active else component.deactivate()
        if scenario.active_objective is not None:
            self._activate_only(scenario.active_objective)
        for name, value in scenario.fixed_variables.items():
            self._fix_variable(name, value)

    def _set_param(self, name: str, value: object) -> None:
        param = getattr(self.model, name)
        if isinstance(value, dict):
            for idx, v in value.items():
                param[idx] = v
        else:
            param.set_value(value)

    def _fix_variable(self, name: str, value: object) -> None:
        var = getattr(self.model, name)
        if isinstance(value, dict):
            for idx, v in value.items():
                var[idx].fix(v)
        else:
            var.fix(value)

    def _activate_only(self, name: str) -> None:
        for objective in self.model.component_objects(pyo.Objective):
            if objective.name == name:
                objective.activate()
            else:
                objective.deactivate()


class ScenarioLoop(YamlComponentBuilder):
    """Decide, a partir de config, entre rodada única ou loop de cenários."""

    _CONFIG_FILENAME = "model_scenarios.yaml"

    def run(
        self,
        model: pyo.ConcreteModel,
        data: ProblemData,
        solver: SolverAdapter,
        profile: str = "default",
    ) -> Result | dict[str, Result]:
        """Roda uma vez (default) ou em loop (enabled: true em model_scenarios.yaml)."""
        try:
            config = self._load_config(self._config_path(data))
        except FileNotFoundError:
            config = {}

        if not config.get("enabled", False):
            return solver.solve(model, profile=config.get("profile", profile))

        scenarios = [self._parse_scenario(spec) for spec in self._require(config, "scenarios")]
        return ScenarioRunner(model, solver).run(
            scenarios, profile=config.get("profile", profile)
        )

    def _parse_scenario(self, spec: dict[str, Any]) -> Scenario:
        return Scenario(
            name=self._require(spec, "name"),
            param_overrides=spec.get("param_overrides", {}),
            active_objective=spec.get("active_objective"),
            active_constraints=spec.get("active_constraints", {}),
            fixed_variables=spec.get("fixed_variables", {}),
            solver_profile=spec.get("solver_profile"),
        )
