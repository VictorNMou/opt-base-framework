import time
from pathlib import Path
from typing import Any, NamedTuple

import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
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
from optframework.solver.solve_compat import solve_with_compat

_CONFIG_DIR = Path(__file__).parent / "config"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Mescla override sobre base; dicts aninhados recursam, o resto é substituído por completo."""
    merged = dict(base)
    for key, value in override.items():
        base_value = merged.get(key)
        if isinstance(base_value, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(base_value, value)
        else:
            merged[key] = value
    return merged


class _Diagnostics(NamedTuple):
    """Agrupa os dois relatórios diagnósticos opcionais de um solve."""

    infeasibility: InfeasibilityReport | None
    sensitivity: SensitivityReport | None


class PyomoAdapter(SolverAdapter, YamlComponentBuilder):
    """Implementação de SolverAdapter via Pyomo, com solver selecionado por perfil."""

    _CONFIG_FILENAME = "model_solver.yaml"

    def __init__(self, config_dir: Path | None = None) -> None:
        """Inicializa sem nenhum resultado ainda armazenado."""
        self._config_dir = config_dir or _CONFIG_DIR
        self._results: Result | None = None

    def solve(
        self,
        model: pyo.ConcreteModel,
        profile: str = "default",
        label: str | None = None,
        data: ProblemData | None = None,
        warmstart: bool = False,
    ) -> Result:
        """Resolve via Pyomo; mescla model_solver.yaml do problema (se houver) sobre o default."""
        config, spec = self._resolve_profile(profile, data)

        reporter = self._build_reporter(config.get("report", {}))
        if reporter is not None:
            reporter.write_before(model, label)

        solver_name, raw_results, metrics = self._run_solver(model, spec, warmstart)
        termination_condition = raw_results.solver.termination_condition
        values = self._extract_values(model, raw_results)

        if reporter is not None:
            reporter.write_after(model, label)

        diagnostics = self._run_diagnostics(
            model, config, solver_name, termination_condition, values, label
        )

        if reporter is not None:
            if diagnostics.infeasibility is not None:
                reporter.write_infeasibility(diagnostics.infeasibility, label)
            if diagnostics.sensitivity is not None:
                reporter.write_sensitivity(diagnostics.sensitivity, label)

        self._results = Result(
            termination_condition=termination_condition,
            values=values,
            infeasibility=diagnostics.infeasibility,
            metrics=metrics,
            sensitivity=diagnostics.sensitivity,
        )
        return self._results

    def _resolve_profile(
        self, profile: str, data: ProblemData | None
    ) -> tuple[dict[str, Any], dict[str, object]]:
        """Carrega e mescla a config de solver, e devolve o spec do profile escolhido."""
        config = self._load_config(self._config_dir / self._CONFIG_FILENAME)
        if data is not None:
            config = _deep_merge(config, self._load_problem_overrides(data))
        profiles = self._require(config, "profiles")
        if profile not in profiles:
            raise KeyError(f"Perfil de solver '{profile}' não encontrado em {self._CONFIG_FILENAME}.")
        return config, profiles[profile]

    def _run_diagnostics(
        self,
        model: pyo.ConcreteModel,
        config: dict[str, Any],
        solver_name: str,
        termination_condition: object,
        values: dict[tuple[str, Any], Any],
        label: str | None,
    ) -> _Diagnostics:
        """Roda infeasibility e sensitivity (cada um só se aplicável) e agrupa os relatórios."""
        infeasibility_report = self._diagnose_infeasibility(
            model, config.get("infeasibility", {}), solver_name, termination_condition, label
        )
        sensitivity_report = self._analyze_sensitivity(
            model, values, config.get("sensitivity", {}), solver_name, label
        )
        return _Diagnostics(infeasibility_report, sensitivity_report)

    def _load_problem_overrides(self, data: ProblemData) -> dict[str, Any]:
        """Carrega o model_solver.yaml do problema, se existir, para mesclar sobre o default."""
        try:
            return self._load_config(self._config_path(data))
        except FileNotFoundError:
            return {}

    def _run_solver(
        self, model: pyo.ConcreteModel, spec: dict[str, object], warmstart: bool
    ) -> tuple[str, object, SolveMetrics]:
        """Resolve via Pyomo medindo tempo de parede; devolve solver_name, raw_results e métricas."""
        solver_name = self._require(spec, "solver_name")
        opt = pyo.SolverFactory(solver_name)
        extra_kwargs = {"tee": spec.get("tee", False), "warmstart": warmstart}
        start = time.perf_counter()
        raw_results = solve_with_compat(
            opt, model, solver_name, spec.get("options", {}), extra_kwargs
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
