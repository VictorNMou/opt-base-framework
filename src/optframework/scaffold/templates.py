"""
Conteúdo dos arquivos gerados por `optframework-new` — ver `optframework.scaffold.cli`.

Cada função devolve o texto de um arquivo, já com um placeholder mínimo que **roda de
verdade** (`sum(x) >= 0` minimizado, resolvido pelo profile default do framework) — a ideia é
provar que o scaffold + a dependência instalada funcionam de ponta a ponta antes do problema
real ser escrito por cima. Nada aqui expressa lógica de negócio: é só o esqueleto descrito em
"Como criar um problema novo" no README, gerado em vez de copiado à mão.
"""

MODEL_SETS_YAML = """\
sets:
  EXEMPLO:
    source: data.exemplo
    # TODO: troque por seus Sets reais (pode ter mais de um). `source` aponta para um
    # atributo iterável do seu ProblemData — ver data_loader.py.
"""

MODEL_PARAMETERS_YAML = """\
parameters: {}
# TODO: um parameter indexado por um Set vira pyo.Param — ver README, seção "Parameters
# com valor default", para o padrão de source/index/default.
"""

MODEL_VARIABLES_YAML = """\
variables:
  x:
    index: [EXEMPLO]
    domain: NonNegativeReals
    # TODO: troque pelas variáveis reais do seu modelo (domain: Reals/NonNegativeReals/
    # Integers/NonNegativeIntegers/Binary).
"""


def render_model_constraints(rules_class: str) -> str:
    """`model_constraints.yaml` — placeholder sem nenhuma constraint declarada."""
    return f"""\
rules_class: {rules_class}
constraints: {{}}
# TODO: uma entrada por constraint, com um método de mesmo nome na classe de Rules acima
# (rules.py). Ver docs/configuration.md, seções "Indexed constraints" e "Attaching vs.
# enabling constraints", para index/enabled opcionais.
"""


def render_model_objective(rules_class: str) -> str:
    """`model_objective.yaml` — um objective trivial (`minimize sum(x)`) só pra rodar."""
    return f"""\
rules_class: {rules_class}
default: objetivo
objectives:
  objetivo:
    sense: minimize
    # TODO: troque 'objetivo' pelo nome real e ajuste sense (minimize/maximize); o método
    # correspondente vive na classe de Objectives acima (rules.py).
"""


def render_data_loader(class_prefix: str) -> str:
    """`data_loader.py` — dataclass mínima que satisfaz o contrato `ProblemData`."""
    return f'''\
from dataclasses import dataclass
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent / "config"


@dataclass
class {class_prefix}Data:
    """Dados do problema (contrato ProblemData). TODO: adicione os campos reais."""

    config_dir: str
    exemplo: list[str]  # TODO: substitua pelos Sets/Parameters de verdade.


def load_data() -> {class_prefix}Data:
    """Monta a instância do problema. TODO: carregue de onde os dados reais vierem."""
    return {class_prefix}Data(
        config_dir=str(_CONFIG_DIR),
        exemplo=["item1"],
    )
'''


def render_rules(class_prefix: str) -> str:
    """`rules.py` — uma classe de Rules (vazia) e uma de Objectives (com o placeholder)."""
    return f'''\
import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData


class {class_prefix}Rules:
    """Regras de constraint do problema — um método por constraint declarada no YAML."""

    def __init__(self, data: ProblemData) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    # TODO: adicione um método por constraint declarada em model_constraints.yaml.
    # def minha_constraint(self, model: pyo.ConcreteModel) -> bool:
    #     return model.x["item1"] <= 10


class {class_prefix}Objectives:
    """Regras de objective do problema — um método por objective declarado no YAML."""

    def __init__(self, data: ProblemData) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def objetivo(self, model: pyo.ConcreteModel) -> object:
        """Placeholder: soma de x. TODO: troque pela função objetivo real."""
        return sum(model.x[e] for e in model.EXEMPLO)
'''


def render_run(package_path: str, nome: str) -> str:
    """
    `run.py` — mesmo workflow de `problems/exemplo_knapsack/run.py`: load → build → solve.

    O corpo do `main()` gerado é, de propósito, quase idêntico ao de
    `problems/exemplo_knapsack/run.py` — é o mesmo workflow padrão (load → build → solve →
    trata infeasible → extrai solução) que todo problema novo usa; o comentário abaixo evita
    que o `pylint` (`duplicate-code`) reclame de um texto template espelhar o exemplo que ele
    templatiza.
    """
    # pylint: disable=duplicate-code
    return f'''\
from optframework.results.export import write_result_json
from optframework.strategy.milp_strategy import MilpStrategy
from {package_path}.data_loader import load_data


def main() -> None:
    """Executa o workflow completo: carrega dados, monta o modelo, resolve e reporta."""
    data = load_data()
    strategy = MilpStrategy()

    model = strategy.build_model(data)
    result = strategy.solve(model, data)

    if result.is_infeasible:
        print("Status:", result.termination_condition)
        print(result.infeasibility.render())
        return

    solution = strategy.extract_solution(result)

    print("Status:", result.termination_condition)
    print("x:", solution["x"])

    write_result_json(result, solution, "reports/{nome}_result.json")


if __name__ == "__main__":
    main()
'''
