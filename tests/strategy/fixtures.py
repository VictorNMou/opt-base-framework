import pyomo.environ as pyo


class FakeRules:
    """Rules fake: soma da produção não pode passar da capacidade total."""

    def __init__(self, data: object) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def capacidade(self, model: pyo.ConcreteModel) -> bool:
        return sum(model.producao[p] for p in model.PRODUTOS) <= model.capacidade_max

    def limite_individual(self, model: pyo.ConcreteModel, produto: str) -> bool:
        """Constraint indexada: cada produto isolado não pode passar da capacidade total."""
        return model.producao[produto] <= model.capacidade_max

    def volume(self, model: pyo.ConcreteModel, produto: str) -> object:
        """Expression reutilizável: volume é o dobro da produção (fórmula fictícia pros testes)."""
        return 2 * model.producao[produto]

    def limite_volume(self, model: pyo.ConcreteModel, produto: str) -> bool:
        """Constraint que referencia a Expression 'volume' — só monta se ela já existir no modelo."""
        return model.volume[produto] <= 2 * model.capacidade_max


class FakeObjectives:
    """Rules fake: maximiza a soma da produção."""

    def __init__(self, data: object) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def maximizar(self, model: pyo.ConcreteModel) -> object:
        return sum(model.producao[p] for p in model.PRODUTOS)
