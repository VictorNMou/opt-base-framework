from typing import Protocol

import pyomo.environ as pyo

from optframework.results.infeasibility import InfeasibilityReport


class InfeasibilityAnalyzer(Protocol):
    """Contrato para qualquer estratégia de diagnóstico de infeasibilidade."""

    def analyze(self, model: pyo.ConcreteModel) -> InfeasibilityReport:
        """Diagnostica a infeasibilidade de um modelo que acabou de resolver como infeasible."""
        ...


_REGISTRY: dict[str, type[InfeasibilityAnalyzer]] = {}


def register(solver_name: str, analyzer: type[InfeasibilityAnalyzer]) -> None:
    """Registra o analisador nativo para um solver_name (normalizado)."""
    _REGISTRY[normalize_solver_name(solver_name)] = analyzer


def get(
    solver_name: str, default: type[InfeasibilityAnalyzer]
) -> type[InfeasibilityAnalyzer]:
    """Devolve o analisador nativo registrado para solver_name, ou default se não houver."""
    return _REGISTRY.get(normalize_solver_name(solver_name), default)


def normalize_solver_name(solver_name: str) -> str:
    """Lowercase + remove sufixo _persistent/_direct, p/ casar 'gurobi_persistent' com 'gurobi'."""
    name = solver_name.lower()
    for suffix in ("_persistent", "_direct"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name
