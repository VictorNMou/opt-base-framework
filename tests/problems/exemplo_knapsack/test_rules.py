import pyomo.environ as pyo

from problems.exemplo_knapsack.data_loader import load_data
from problems.exemplo_knapsack.rules import KnapsackObjectives, KnapsackRules


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.ITEMS = pyo.Set(initialize=["A", "B", "C"])
    model.peso = pyo.Param(model.ITEMS, initialize={"A": 10, "B": 20, "C": 30})
    model.capacidade_max = pyo.Param(initialize=50)
    model.selecionado = pyo.Var(model.ITEMS, domain=pyo.Binary)
    return model


def test_limite_capacidade_returns_true_when_within_capacity() -> None:
    model = _new_model()
    model.selecionado["A"].fix(1)
    model.selecionado["B"].fix(1)
    model.selecionado["C"].fix(0)
    rules = KnapsackRules(load_data())

    assert pyo.value(rules.limite_capacidade(model))


def test_limite_capacidade_returns_false_when_over_capacity() -> None:
    model = _new_model()
    model.selecionado["A"].fix(1)
    model.selecionado["B"].fix(1)
    model.selecionado["C"].fix(1)
    rules = KnapsackRules(load_data())

    assert not pyo.value(rules.limite_capacidade(model))


def test_limite_capacidade_attaches_as_real_constraint_via_framework() -> None:
    model = _new_model()
    rules = KnapsackRules(load_data())

    model.limite_capacidade = pyo.Constraint(rule=rules.limite_capacidade)

    assert isinstance(model.limite_capacidade, pyo.Constraint)


def test_maximizar_valor_returns_total_value_expression() -> None:
    model = _new_model()
    model.valor = pyo.Param(model.ITEMS, initialize={"A": 60, "B": 100, "C": 120})
    model.selecionado["A"].fix(0)
    model.selecionado["B"].fix(1)
    model.selecionado["C"].fix(1)
    objectives = KnapsackObjectives(load_data())

    expr = objectives.maximizar_valor(model)

    assert pyo.value(expr) == 220


def test_maximizar_valor_attaches_as_real_objective_via_framework() -> None:
    model = _new_model()
    model.valor = pyo.Param(model.ITEMS, initialize={"A": 60, "B": 100, "C": 120})
    objectives = KnapsackObjectives(load_data())

    model.maximizar_valor = pyo.Objective(rule=objectives.maximizar_valor, sense=pyo.maximize)

    assert isinstance(model.maximizar_valor, pyo.Objective)
