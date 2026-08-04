import pyomo.environ as pyo

from optframework.constraints.base import ConstraintRule
from optframework.core.problem_data import ProblemData


class CapacityConstraint(ConstraintRule):
    """Exemplo de constraint de capacidade para o problema de produção."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        """Constrói e anexa a constraint de capacidade ao modelo."""
