from pathlib import Path
from typing import Any

import pyomo.environ as pyo

from optframework.core.yaml_component import YamlComponentBuilder
from optframework.results.infeasibility import InfeasibilityReport
from optframework.results.result import INFEASIBLE_TERMINATION_CONDITIONS, Result
from optframework.solver.adapter import SolverAdapter
from optframework.solver.infeasibility.elastic import ElasticRelaxationAnalyzer
from optframework.solver.infeasibility.registry import get as get_infeasibility_analyzer
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

        solver_name = self._require(spec, "solver_name")
        opt = pyo.SolverFactory(solver_name)
        opt.options.update(spec.get("options", {}))
        raw_results = opt.solve(
            model, tee=spec.get("tee", False), symbolic_solver_labels=True, load_solutions=False
        )
        termination_condition = raw_results.solver.termination_condition

        values: dict[tuple[str, Any], Any] = {}
        if len(raw_results.solution) > 0:
            model.solutions.load_from(raw_results)
            values = {
                (var.parent_component().local_name, var.index()): pyo.value(var)
                for var in model.component_data_objects(pyo.Var, active=True)
            }

        if reporter is not None:
            reporter.write_after(model, label)

        infeasibility_report = self._diagnose_infeasibility(
            model, config.get("infeasibility", {}), solver_name, termination_condition, label
        )

        if reporter is not None and infeasibility_report is not None:
            reporter.write_infeasibility(infeasibility_report, label)

        self._results = Result(
            termination_condition=termination_condition,
            values=values,
            infeasibility=infeasibility_report,
        )
        return self._results

    def _diagnose_infeasibility(
        self,
        model: pyo.ConcreteModel,
        infeasibility_spec: dict[str, object],
        solver_name: str,
        termination_condition: object,
        label: str | None,
    ) -> InfeasibilityReport | None:
        """Roda o analisador de infeasibilidade (nativo ou elástico) quando o solve for infeasible."""
        if not infeasibility_spec.get("enabled", True):
            return None
        if termination_condition not in INFEASIBLE_TERMINATION_CONDITIONS:
            return None
        analyzer_cls = get_infeasibility_analyzer(solver_name, default=ElasticRelaxationAnalyzer)
        analyzer = analyzer_cls(
            solver_name=solver_name,
            options=infeasibility_spec.get("options", {}),
            tolerance=float(infeasibility_spec.get("tolerance", 1e-6)),
            output_dir=infeasibility_spec.get("output_dir", "reports"),
            label=label,
        )
        return analyzer.analyze(model)

    def get_results(self) -> Result:
        """Devolve o resultado bruto do último solve."""
        if self._results is None:
            raise ValueError("Nenhum solve foi executado ainda.")
        return self._results

    def _build_reporter(self, report_spec: dict[str, object]) -> Reporter | None:
        if not report_spec.get("enabled", False):
            return None
        return Reporter(self._require(report_spec, "output_dir"))
