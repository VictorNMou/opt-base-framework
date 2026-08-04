import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.objective.objective import ObjectiveRule


class MaximizeValue(ObjectiveRule):
    """Maximiza o valor total dos itens selecionados na mochila."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> object:
        """Devolve a expressão de valor total (não se auto-anexa ao modelo)."""
        return sum(model.valor[i] * model.selecionado[i] for i in model.ITEMS)
