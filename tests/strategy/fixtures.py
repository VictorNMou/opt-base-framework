import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules


class FakeRules(ConstraintRules):
    """Rules fake: soma da produção não pode passar da capacidade total."""

    def capacidade(self, model: pyo.ConcreteModel) -> bool:
        return sum(model.producao[p] for p in model.PRODUTOS) <= model.capacidade_max


class FakeObjectives:
    """Rules fake: maximiza a soma da produção."""

    def __init__(self, data: object) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def maximizar(self, model: pyo.ConcreteModel) -> object:
        return sum(model.producao[p] for p in model.PRODUTOS)
