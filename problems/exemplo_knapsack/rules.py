import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules


class KnapsackRules(ConstraintRules):
    """Regras de constraint do problema de knapsack — uma constraint por método."""

    def limite_capacidade(self, model: pyo.ConcreteModel) -> bool:
        """Peso total dos itens selecionados não pode passar da capacidade da mochila."""
        return (
            sum(model.peso[i] * model.selecionado[i] for i in model.ITEMS)
            <= model.capacidade_max
        )
