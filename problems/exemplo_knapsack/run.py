from optframework.results.export import write_result_json
from optframework.strategy.milp_strategy import MilpStrategy
from problems.exemplo_knapsack.data_loader import load_data


def main() -> None:
    """Executa o workflow completo: carrega dados, monta o modelo, resolve e reporta."""
    data = load_data()
    strategy = MilpStrategy()

    model = strategy.build_model(data)
    result = strategy.solve(model)

    if result.is_infeasible:
        print("Status:", result.termination_condition)
        print(result.infeasibility.render())
        return

    solution = strategy.extract_solution(result)

    selecionados = [
        item for item, valor in solution["selecionado"].items() if valor > 0.5
    ]
    valor_total = sum(data.valor[item] for item in selecionados)

    print("Status:", result.termination_condition)
    print("Itens selecionados:", selecionados)
    print("Valor total:", valor_total)

    write_result_json(result, solution, "reports/exemplo_knapsack_result.json")


if __name__ == "__main__":
    main()
