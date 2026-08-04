import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData


class MarkerRule:
    """Rule fake: marca no modelo que foi chamada."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        model.add_component("marker_called", pyo.Param(initialize=1))


class SumConstraintRule:
    """Rule fake: anexa um pyo.Constraint real sobre uma Var pré-existente."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        model.add_component("limite", pyo.Constraint(expr=model.x <= 10))
