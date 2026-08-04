import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules
from optframework.objective.rules import ObjectiveRules


class KnapsackRules(ConstraintRules):
    """Regras de constraint do problema de knapsack — uma constraint por método."""

    def limite_capacidade(self, model: pyo.ConcreteModel) -> bool:
        """Peso total dos itens selecionados não pode passar da capacidade da mochila."""
        return (
            sum(model.peso[i] * model.selecionado[i] for i in model.ITEMS)
            <= model.capacidade_max
        )


class KnapsackObjectives(ObjectiveRules):
    """Regras de objective do problema de knapsack — um objective por método."""

    def maximizar_valor(self, model: pyo.ConcreteModel) -> object:
        """Valor total dos itens selecionados na mochila."""
        return sum(model.valor[i] * model.selecionado[i] for i in model.ITEMS)
