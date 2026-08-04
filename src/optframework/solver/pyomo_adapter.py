import time
from pathlib import Path
from typing import Any

import pyomo.environ as pyo

from optframework.core.yaml_component import YamlComponentBuilder
from optframework.results.infeasibility import InfeasibilityReport
from optframework.results.metrics import SolveMetrics
from optframework.results.result import INFEASIBLE_TERMINATION_CONDITIONS, Result
from optframework.results.sensitivity import SensitivityReport
from optframework.solver.adapter import SolverAdapter
from optframework.solver.infeasibility.elastic import ElasticRelaxationAnalyzer
from optframework.solver.infeasibility.registry import get as get_infeasibility_analyzer
from optframework.solver.metrics import build_solve_metrics
from optframework.solver.reporter import Reporter
from optframework.solver.sensitivity import SensitivityAnalyzer

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

        solver_name, raw_results, metrics = self._run_solver(model, spec)
        termination_condition = raw_results.solver.termination_condition
        values = self._extract_values(model, raw_results)

        if reporter is not None:
            reporter.write_after(model, label)

        infeasibility_report = self._diagnose_infeasibility(
            model, config.get("infeasibility", {}), solver_name, termination_condition, label
        )
        sensitivity_report = self._analyze_sensitivity(
            model, values, config.get("sensitivity", {}), solver_name, label
        )

        if reporter is not None:
            if infeasibility_report is not None:
                reporter.write_infeasibility(infeasibility_report, label)
            if sensitivity_report is not None:
                reporter.write_sensitivity(sensitivity_report, label)

        self._results = Result(
            termination_condition=termination_condition,
            values=values,
            infeasibility=infeasibility_report,
            metrics=metrics,
            sensitivity=sensitivity_report,
        )
        return self._results

    def _run_solver(
        self, model: pyo.ConcreteModel, spec: dict[str, object]
    ) -> tuple[str, object, SolveMetrics]:
        """Resolve via Pyomo medindo tempo de parede; devolve solver_name, raw_results e métricas."""
        solver_name = self._require(spec, "solver_name")
        opt = pyo.SolverFactory(solver_name)
        opt.options.update(spec.get("options", {}))
        start = time.perf_counter()
        raw_results = opt.solve(
            model, tee=spec.get("tee", False), symbolic_solver_labels=True, load_solutions=False
        )
        metrics = build_solve_metrics(raw_results, time.perf_counter() - start)
        return solver_name, raw_results, metrics

    def _extract_values(
        self, model: pyo.ConcreteModel, raw_results: object
    ) -> dict[tuple[str, Any], Any]:
        """Carrega a solução no model e extrai os valores resolvidos, ou {} se infeasible."""
        if len(raw_results.solution) == 0:
            return {}
        model.solutions.load_from(raw_results)
        return {
            (var.parent_component().local_name, var.index()): pyo.value(var)
            for var in model.component_data_objects(pyo.Var, active=True)
        }

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

    def _analyze_sensitivity(
        self,
        model: pyo.ConcreteModel,
        values: dict[tuple[str, Any], Any],
        sensitivity_spec: dict[str, object],
        solver_name: str,
        label: str | None,
    ) -> SensitivityReport | None:
        """Roda o analisador de sensibilidade quando habilitado e uma solução foi encontrada."""
        if not sensitivity_spec.get("enabled", False):
            return None
        if not values:
            return None
        analyzer = SensitivityAnalyzer(
            solver_name=solver_name, options=sensitivity_spec.get("options", {}), label=label
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
