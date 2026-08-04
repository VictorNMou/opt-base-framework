from typing import Protocol

import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData


class ConstraintRule(Protocol):
    """Contrato para uma família de constraints do modelo."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        """Constrói e anexa a constraint ao modelo."""
        ...
