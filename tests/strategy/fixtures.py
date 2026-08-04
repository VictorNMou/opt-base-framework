import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules
from optframework.objective.rules import ObjectiveRules


class FakeRules(ConstraintRules):
    """Rules fake: soma da produção não pode passar da capacidade total."""

    def capacidade(self, model: pyo.ConcreteModel) -> bool:
        return sum(model.producao[p] for p in model.PRODUTOS) <= model.capacidade_max


class FakeObjectives(ObjectiveRules):
    """Rules fake: maximiza a soma da produção."""

    def maximizar(self, model: pyo.ConcreteModel) -> object:
        return sum(model.producao[p] for p in model.PRODUTOS)
