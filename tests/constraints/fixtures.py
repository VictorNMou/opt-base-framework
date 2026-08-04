import pyomo.environ as pyo

from optframework.constraints.rules import ConstraintRules


class FakeRules(ConstraintRules):
    """Rules fake: uma constraint trivial e uma constraint real sobre uma Var pré-existente."""

    def marker(self, model: object) -> object:
        return pyo.Constraint.Feasible

    def limite(self, model: object) -> bool:
        return model.x <= 10
