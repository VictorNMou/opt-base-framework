import pyomo.environ as pyo

from optframework.results.export import write_result_json
from optframework.strategy import registry
from problems.exemplo_precificacao.data_loader import PrecificacaoData, load_data
from problems.exemplo_precificacao.rules import PrecificacaoRules


def main() -> None:
    """Executa o workflow completo: carrega dados, monta o modelo NLP, resolve e reporta."""
    # pylint: disable=duplicate-code
    data = load_data()
    strategy = registry.get("nlp")()

    model = strategy.build_model(data)
    _set_initial_point_and_bounds(model, data)

    result = strategy.solve(model, data)

    if result.is_infeasible:
        print("Status:", result.termination_condition)
        print(result.infeasibility.render())
        return

    solution = strategy.extract_solution(result)
    rules = PrecificacaoRules(data)

    print("Status:", result.termination_condition)
    margem_total = 0.0
    for produto in data.produtos:
        preco = solution["p"][produto]
        demanda = pyo.value(rules.demanda(model, produto))
        margem = (preco - data.custo[produto]) * demanda
        margem_total += margem
        print(f"{produto}: preço=R${preco:.2f} demanda={demanda:.1f} margem=R${margem:,.2f}")
    print(f"Margem total: R${margem_total:,.2f}")

    write_result_json(result, solution, "reports/exemplo_precificacao_result.json")


def _set_initial_point_and_bounds(model: pyo.ConcreteModel, data: PrecificacaoData) -> None:
    """Define ponto inicial e faixa de preço — sem equivalente em model_variables.yaml (só domain/index)."""
    # ipopt precisa de ponto de partida estritamente positivo; sem faixa de preço o problema
    # fica sem ótimo finito (elasticidade cruzada positiva dispara a margem se um preço -> infinito).
    for produto in model.PRODUTOS:
        preco_base = data.preco_base[produto]
        model.p[produto].set_value(preco_base)
        model.p[produto].setlb(0.5 * preco_base)
        model.p[produto].setub(1.5 * preco_base)


if __name__ == "__main__":
    main()
