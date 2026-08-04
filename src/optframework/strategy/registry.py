from typing import Any, Protocol

import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.results.result import Result


class OptimizationStrategy(Protocol):
    """Contrato de alto nível que cada classe de otimização (MILP, CP, ...) implementa."""

    def build_model(self, data: ProblemData) -> pyo.ConcreteModel:
        """Monta o modelo para esta classe de otimização."""
        ...

    def solve(self, model: pyo.ConcreteModel) -> Result:
        """Resolve o modelo montado."""
        ...

    def extract_solution(self, result: Result) -> dict[str, Any]:
        """Extrai a solução do resultado bruto do solve."""
        ...


_REGISTRY: dict[str, type[OptimizationStrategy]] = {}


def register(optimization_type: str, strategy: type[OptimizationStrategy]) -> None:
    """Registra uma estratégia para um optimization_type."""
    _REGISTRY[optimization_type] = strategy


def get(optimization_type: str) -> type[OptimizationStrategy]:
    """Devolve a estratégia registrada para um optimization_type."""
    return _REGISTRY[optimization_type]
