from pathlib import Path

import pyomo.environ as pyo

from optframework.results.infeasibility import InfeasibilityReport
from optframework.solver.infeasibility.registry import normalize_solver_name


class NativeIISAnalyzer:
    """Diagnostica infeasibilidade via IIS nativo do solver (Gurobi/CPLEX), usando pyomo.contrib.iis."""

    def __init__(
        self,
        solver_name: str,
        options: dict[str, object] | None = None,
        tolerance: float = 1e-6,
        output_dir: str | None = None,
        label: str | None = None,
    ) -> None:
        """Guarda o solver_name (usado para escolher o backend nativo), saída do IIS e o label."""
        self.solver_name = solver_name
        self.options = options or {}
        self.tolerance = tolerance
        self.output_dir = output_dir or "reports"
        self.label = label

    def analyze(self, model: pyo.ConcreteModel) -> InfeasibilityReport:
        """Grava o IIS nativo do solver em disco e devolve o caminho do arquivo no relatório."""
        try:
            from pyomo.contrib.iis import write_iis
        except ImportError as exc:
            raise RuntimeError(
                "pyomo.contrib.iis não disponível nesta instalação do Pyomo."
            ) from exc

        solver_key = normalize_solver_name(self.solver_name)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        suffix = f"_{self.label}" if self.label else ""
        candidate = str(
            Path(self.output_dir) / f"infeasibility_iis_{solver_key}{suffix}"
        )

        try:
            iis_file = write_iis(model, candidate, solver=solver_key)
        except ImportError as exc:
            raise RuntimeError(
                f"Diagnóstico nativo requer o pacote opcional do solver '{solver_key}' "
                f"instalado (ex.: `uv pip install .[{solver_key}]`)."
            ) from exc

        return InfeasibilityReport(method=f"native_iis:{solver_key}", iis_file=iis_file)
