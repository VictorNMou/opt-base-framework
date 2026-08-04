import pyomo.environ as pyo

from problems.exemplo_knapsack.data_loader import load_data
from problems.exemplo_knapsack.objective_impl import MaximizeValue


def test_build_returns_total_value_expression() -> None:
    model = pyo.ConcreteModel()
    model.ITEMS = pyo.Set(initialize=["A", "B", "C"])
    model.valor = pyo.Param(model.ITEMS, initialize={"A": 60, "B": 100, "C": 120})
    model.selecionado = pyo.Var(model.ITEMS, domain=pyo.Binary)
    model.selecionado["A"].fix(0)
    model.selecionado["B"].fix(1)
    model.selecionado["C"].fix(1)
    data = load_data()

    expr = MaximizeValue().build(model, data)

    assert pyo.value(expr) == 220
