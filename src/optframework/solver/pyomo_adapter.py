from pathlib import Path

import pyomo.environ as pyo

from optframework.core.yaml_component import YamlComponentBuilder
from optframework.results.result import Result
from optframework.solver.adapter import SolverAdapter

_CONFIG_DIR = Path(__file__).parent / "config"


class PyomoAdapter(SolverAdapter, YamlComponentBuilder):
    """Implementação de SolverAdapter via Pyomo, com solver selecionado por perfil."""

    _CONFIG_FILENAME = "model_solver.yaml"

    def __init__(self) -> None:
        """Inicializa sem nenhum resultado ainda armazenado."""
        self._results: Result | None = None

    def solve(self, model: pyo.ConcreteModel, profile: str = "default") -> Result:
        """Resolve o modelo via Pyomo, usando o perfil configurado em model_solver.yaml."""
        config = self._load_config(_CONFIG_DIR / self._CONFIG_FILENAME)
        profiles = self._require(config, "profiles")
        if profile not in profiles:
            raise KeyError(f"Perfil de solver '{profile}' não encontrado em {self._CONFIG_FILENAME}.")
        spec = profiles[profile]

        opt = pyo.SolverFactory(self._require(spec, "solver_name"))
        opt.options.update(spec.get("options", {}))
        raw_results = opt.solve(
            model, tee=spec.get("tee", False), symbolic_solver_labels=True
        )

        values = {
            str(var): pyo.value(var)
            for var in model.component_data_objects(pyo.Var, active=True)
        }
        self._results = Result(
            termination_condition=raw_results.solver.termination_condition,
            values=values,
        )
        return self._results

    def get_results(self) -> Result:
        """Devolve o resultado bruto do último solve."""
        if self._results is None:
            raise ValueError("Nenhum solve foi executado ainda.")
        return self._results
