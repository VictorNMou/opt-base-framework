import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData


class PrecificacaoRules:
    """Regras de constraint e objective do problema de precificação — compartilham a demanda."""

    def __init__(self, data: ProblemData) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def demanda(self, model: pyo.ConcreteModel, produto: str) -> object:
        """Demanda de `produto` via elasticidade constante: própria vezes cruzada dos demais."""
        fator = (
            model.p[produto] / model.preco_base[produto]
        ) ** model.elasticidade_propria[produto]
        for outro in model.PRODUTOS:
            if outro != produto:
                fator *= (
                    model.p[outro] / model.preco_base[outro]
                ) ** model.elasticidade_cruzada[produto, outro]
        return model.quantidade_base[produto] * fator

    def capacidade_producao(self, model: pyo.ConcreteModel) -> bool:
        """Demanda total somada entre produtos não pode passar da capacidade de produção."""
        total = sum(self.demanda(model, produto) for produto in model.PRODUTOS)
        return total <= model.capacidade_total

    def margem_total(self, model: pyo.ConcreteModel) -> object:
        """Margem total: (preço - custo) vezes demanda, somada entre produtos."""
        return sum(
            (model.p[produto] - model.custo[produto]) * self.demanda(model, produto)
            for produto in model.PRODUTOS
        )
