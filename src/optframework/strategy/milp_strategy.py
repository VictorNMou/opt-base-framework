from typing import Any

import pyomo.environ as pyo

from optframework.core.model import Model
from optframework.core.problem_data import ProblemData
from optframework.results.result import Result
from optframework.solver.pyomo_adapter import PyomoAdapter


class MilpStrategy:
    """Estratégia de otimização para problemas LP/MILP."""

    def build_model(self, data: ProblemData) -> pyo.ConcreteModel:
        """Monta o modelo MILP via Model."""
        return Model(data).build()

    def solve(self, model: pyo.ConcreteModel) -> Result:
        """Resolve o modelo via PyomoAdapter."""
        return PyomoAdapter().solve(model)

    def extract_solution(self, result: Result) -> dict[str, Any]:
        """Reagrupa Result.values (chave (nome, índice)) por variável."""
        solution: dict[str, Any] = {}
        for (name, index), value in result.values.items():
            if index is None:
                solution[name] = value
            else:
                solution.setdefault(name, {})[index] = value
        return solution
