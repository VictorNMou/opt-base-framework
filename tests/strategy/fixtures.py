import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData


class CapacityConstraint:
    """Rule fake: soma da produção não pode passar da capacidade total."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        model.add_component(
            "capacidade",
            pyo.Constraint(
                expr=sum(model.producao[p] for p in model.PRODUTOS) <= model.capacidade_max
            ),
        )


class MaximizeProducao:
    """Rule fake: maximiza a soma da produção."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> object:
        return sum(model.producao[p] for p in model.PRODUTOS)
