import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules
from optframework.core.problem_data import ProblemData


class FakeRules(ConstraintRules):
    """Rules fake: soma da produção não pode passar da capacidade total."""

    def capacidade(self, model: pyo.ConcreteModel) -> bool:
        return sum(model.producao[p] for p in model.PRODUTOS) <= model.capacidade_max


class MaximizeProducao:
    """Rule fake: maximiza a soma da produção."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> object:
        return sum(model.producao[p] for p in model.PRODUTOS)
