import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules
from optframework.core.problem_data import ProblemData


class KnapsackRules(ConstraintRules):
    """Regras de constraint do problema de knapsack — uma constraint por método."""

    def limite_capacidade(self, model: pyo.ConcreteModel) -> bool:
        """Peso total dos itens selecionados não pode passar da capacidade da mochila."""
        return (
            sum(model.peso[i] * model.selecionado[i] for i in model.ITEMS)
            <= model.capacidade_max
        )


class KnapsackObjectives:
    """Regras de objective do problema de knapsack — um objective por método."""

    def __init__(self, data: ProblemData) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def maximizar_valor(self, model: pyo.ConcreteModel) -> object:
        """Valor total dos itens selecionados na mochila."""
        return sum(model.valor[i] * model.selecionado[i] for i in model.ITEMS)
