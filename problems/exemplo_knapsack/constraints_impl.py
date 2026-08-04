import pyomo.environ as pyo

from optframework.constraints.base import ConstraintRule
from optframework.core.problem_data import ProblemData


class CapacityConstraint(ConstraintRule):
    """Peso total dos itens selecionados não pode passar da capacidade da mochila."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        """Constrói e anexa a constraint de capacidade ao modelo."""
        model.add_component(
            "limite_capacidade",
            pyo.Constraint(
                expr=sum(model.peso[i] * model.selecionado[i] for i in model.ITEMS)
                <= model.capacidade_max
            ),
        )
