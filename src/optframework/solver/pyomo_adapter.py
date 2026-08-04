from pathlib import Path

import pyomo.environ as pyo

from optframework.core.yaml_component import YamlComponentBuilder
from optframework.results.result import Result
from optframework.solver.adapter import SolverAdapter
from optframework.solver.reporter import Reporter

_CONFIG_DIR = Path(__file__).parent / "config"


class PyomoAdapter(SolverAdapter, YamlComponentBuilder):
    """Implementação de SolverAdapter via Pyomo, com solver selecionado por perfil."""

    _CONFIG_FILENAME = "model_solver.yaml"

    def __init__(self, config_dir: Path | None = None) -> None:
        """Inicializa sem nenhum resultado ainda armazenado."""
        self._config_dir = config_dir or _CONFIG_DIR
        self._results: Result | None = None

    def solve(
        self, model: pyo.ConcreteModel, profile: str = "default", label: str | None = None
    ) -> Result:
        """Resolve o modelo via Pyomo, usando o perfil configurado em model_solver.yaml."""
        config = self._load_config(self._config_dir / self._CONFIG_FILENAME)
        profiles = self._require(config, "profiles")
        if profile not in profiles:
            raise KeyError(f"Perfil de solver '{profile}' não encontrado em {self._CONFIG_FILENAME}.")
        spec = profiles[profile]

        reporter = self._build_reporter(config.get("report", {}))
        if reporter is not None:
            reporter.write_before(model, label)

        opt = pyo.SolverFactory(self._require(spec, "solver_name"))
        opt.options.update(spec.get("options", {}))
        raw_results = opt.solve(
            model, tee=spec.get("tee", False), symbolic_solver_labels=True
        )

        if reporter is not None:
            reporter.write_after(model, label)

        values = {
            (var.parent_component().local_name, var.index()): pyo.value(var)
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

    def _build_reporter(self, report_spec: dict[str, object]) -> Reporter | None:
        if not report_spec.get("enabled", False):
            return None
        return Reporter(self._require(report_spec, "output_dir"))
