import pyomo.environ as pyo

from problems.exemplo_knapsack.constraints_impl import CapacityConstraint
from problems.exemplo_knapsack.data_loader import load_data


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.ITEMS = pyo.Set(initialize=["A", "B", "C"])
    model.peso = pyo.Param(model.ITEMS, initialize={"A": 10, "B": 20, "C": 30})
    model.capacidade_max = pyo.Param(initialize=50)
    model.selecionado = pyo.Var(model.ITEMS, domain=pyo.Binary)
    return model


def test_build_attaches_limite_capacidade_constraint() -> None:
    model = _new_model()
    data = load_data()

    CapacityConstraint().build(model, data)

    assert isinstance(model.limite_capacidade, pyo.Constraint)


def test_constraint_expression_matches_weighted_sum() -> None:
    model = _new_model()
    data = load_data()
    CapacityConstraint().build(model, data)

    model.selecionado["A"].fix(1)
    model.selecionado["B"].fix(1)
    model.selecionado["C"].fix(0)

    body_value = pyo.value(model.limite_capacidade.body)

    assert body_value == 30
