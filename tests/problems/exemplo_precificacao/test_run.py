import pyomo.environ as pyo
import pytest

from optframework.strategy import registry
from problems.exemplo_precificacao.data_loader import load_data
from problems.exemplo_precificacao.rules import PrecificacaoRules
from problems.exemplo_precificacao.run import _set_initial_point_and_bounds, main

pytestmark = pytest.mark.skipif(
    not pyo.SolverFactory("ipopt").available(exception_flag=False),
    reason="ipopt não instalado neste ambiente",
)


def test_precificacao_solves_to_finite_optimum_within_price_bounds() -> None:
    # pylint: disable=duplicate-code
    data = load_data()
    strategy = registry.get("nlp")()
    rules = PrecificacaoRules(data)

    model = strategy.build_model(data)
    _set_initial_point_and_bounds(model, data)
    result = strategy.solve(model, data)
    solution = strategy.extract_solution(result)

    assert result.termination_condition == pyo.TerminationCondition.optimal

    margem_total = 0.0
    for produto in data.produtos:
        preco = solution["p"][produto]
        tolerancia = 1e-3
        assert 0.5 * data.preco_base[produto] - tolerancia <= preco
        assert preco <= 1.5 * data.preco_base[produto] + tolerancia
        demanda = pyo.value(rules.demanda(model, produto))
        assert demanda > 0
        margem_total += (preco - data.custo[produto]) * demanda

    assert margem_total > 0


def test_main_runs_without_error() -> None:
    main()
