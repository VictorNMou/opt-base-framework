import pyomo.environ as pyo

from optframework.strategy.milp_strategy import MilpStrategy
from problems.exemplo_knapsack.data_loader import load_data
from problems.exemplo_knapsack.run import main


def test_knapsack_solves_to_known_optimal() -> None:
    # pylint: disable=duplicate-code
    data = load_data()
    strategy = MilpStrategy()

    model = strategy.build_model(data)
    result = strategy.solve(model, data)
    solution = strategy.extract_solution(result)

    assert result.termination_condition == pyo.TerminationCondition.optimal

    selecionados = {
        item for item, valor in solution["selecionado"].items() if valor > 0.5
    }
    assert selecionados == {"B", "C"}

    valor_total = sum(data.valor[item] for item in selecionados)
    assert valor_total == 220


def test_main_runs_without_error() -> None:
    main()
