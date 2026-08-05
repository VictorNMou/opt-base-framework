import pyomo.environ as pyo


class FakeRules:
    """Rules fake: uma constraint trivial e uma constraint real sobre uma Var pré-existente."""

    def __init__(self, data: object) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def marker(self, model: object) -> object:
        return pyo.Constraint.Feasible

    def limite(self, model: object) -> bool:
        return model.x <= 10

    def limite_por_item(self, model: object, item: object) -> object:
        return model.y[item] <= 10
