import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData


class CountingRule:
    """Rule fake: conta quantas vezes build() foi chamado, para provar cache."""

    call_count = 0

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> object:
        CountingRule.call_count += 1
        return model.x


class OtherRule:
    """Rule fake: uma segunda expressão, para o cenário de dois perfis."""

    def build(self, model: pyo.ConcreteModel, data: ProblemData) -> object:
        return model.y
