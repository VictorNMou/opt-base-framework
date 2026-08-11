import pyomo.environ as pyo
import pytest

from problems.exemplo_precificacao.data_loader import load_data
from problems.exemplo_precificacao.rules import PrecificacaoRules


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.PRODUTOS = pyo.Set(initialize=["A", "B"])
    model.preco_base = pyo.Param(model.PRODUTOS, initialize={"A": 10.0, "B": 20.0})
    model.quantidade_base = pyo.Param(
        model.PRODUTOS, initialize={"A": 100.0, "B": 50.0}
    )
    model.custo = pyo.Param(model.PRODUTOS, initialize={"A": 5.0, "B": 8.0})
    model.elasticidade_propria = pyo.Param(
        model.PRODUTOS, initialize={"A": -2.0, "B": -1.5}
    )
    model.elasticidade_cruzada = pyo.Param(
        model.PRODUTOS, model.PRODUTOS, initialize={("A", "B"): 0.4, ("B", "A"): 0.3}
    )
    model.capacidade_total = pyo.Param(initialize=1000.0, mutable=True)
    model.p = pyo.Var(model.PRODUTOS, domain=pyo.NonNegativeReals)
    return model


def test_demanda_equals_base_quantity_when_price_at_base() -> None:
    model = _new_model()
    model.p["A"].fix(10.0)
    model.p["B"].fix(20.0)
    rules = PrecificacaoRules(load_data())

    assert pyo.value(rules.demanda(model, "A")) == pytest.approx(100.0)
    assert pyo.value(rules.demanda(model, "B")) == pytest.approx(50.0)


def test_demanda_falls_when_own_price_rises() -> None:
    model = _new_model()
    model.p["A"].fix(20.0)
    model.p["B"].fix(20.0)
    rules = PrecificacaoRules(load_data())

    assert pyo.value(rules.demanda(model, "A")) < 100.0


def test_demanda_rises_when_cross_price_rises() -> None:
    model = _new_model()
    model.p["A"].fix(10.0)
    model.p["B"].fix(40.0)
    rules = PrecificacaoRules(load_data())

    assert pyo.value(rules.demanda(model, "A")) > 100.0


def test_capacidade_producao_returns_true_when_within_capacity() -> None:
    model = _new_model()
    model.p["A"].fix(10.0)
    model.p["B"].fix(20.0)
    rules = PrecificacaoRules(load_data())

    assert pyo.value(rules.capacidade_producao(model))


def test_capacidade_producao_returns_false_when_over_capacity() -> None:
    model = _new_model()
    model.capacidade_total.set_value(1.0)
    model.p["A"].fix(10.0)
    model.p["B"].fix(20.0)
    rules = PrecificacaoRules(load_data())

    assert not pyo.value(rules.capacidade_producao(model))


def test_capacidade_producao_attaches_as_real_constraint_via_framework() -> None:
    model = _new_model()
    rules = PrecificacaoRules(load_data())

    model.capacidade_producao = pyo.Constraint(rule=rules.capacidade_producao)

    assert isinstance(model.capacidade_producao, pyo.Constraint)


def test_margem_total_matches_manual_calculation_at_base_price() -> None:
    model = _new_model()
    model.p["A"].fix(10.0)
    model.p["B"].fix(20.0)
    rules = PrecificacaoRules(load_data())

    margem = pyo.value(rules.margem_total(model))

    esperado = (10.0 - 5.0) * 100.0 + (20.0 - 8.0) * 50.0
    assert margem == pytest.approx(esperado)


def test_margem_total_attaches_as_real_objective_via_framework() -> None:
    model = _new_model()
    rules = PrecificacaoRules(load_data())

    model.margem_total = pyo.Objective(rule=rules.margem_total, sense=pyo.maximize)

    assert isinstance(model.margem_total, pyo.Objective)
