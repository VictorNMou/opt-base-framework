# Opt Base Framework

Framework Python para problemas de otimização (LP/MILP via [Pyomo](https://www.pyomo.org/)),
com núcleo genérico *config-driven* e reaplicável para qualquer problema novo sem tocar no
código do framework.

## Quickstart

```bash
uv sync
uv run python -m problems.exemplo_knapsack.run
```

Saída esperada (instância clássica de knapsack 0/1 — pesos `[10, 20, 30]`, valores
`[60, 100, 120]`, capacidade `50`):

```
Status: optimal
Itens selecionados: ['B', 'C']
Valor total: 220
```

## Arquitetura

O núcleo (`src/optframework/`) monta o modelo em camadas, cada uma lendo sua própria
configuração YAML do problema:

| Camada | O que é | Onde mora a lógica |
|---|---|---|
| Validação de config | Checa os 5 YAMLs do problema antes de montar qualquer `pyo.Constraint` | Automática, sempre ligada, roda no início de `Model.build()`; agrega **todos** os problemas encontrados num único `ConfigValidationError` em vez de falhar um de cada vez; `core/validation.py` |
| `Sets`/`Parameters`/`Variables` | Metadados puros (índices, domínio, fonte de dado) | 100% YAML — sem código Python por problema |
| `Constraints`/`Objective` | Matemática Pyomo (expressões) | Uma classe `Rules` por problema, um **método nomeado** por constraint/objective |
| `Solver` | Resolve via `pyo.SolverFactory` | Perfis (`default`/`optimal`/`faster_not_optimal`) em `model_solver.yaml` de nível framework, usando [HiGHS](https://highs.dev/) (`highspy`, sem binário de sistema); um `model_solver.yaml` opcional em `problems/<nome>/config/` faz *deep merge* por cima (só as chaves declaradas sobrescrevem, recursivamente) |
| `ScenarioLoop` | Resolve a mesma instância várias vezes, mutando parâmetros/ativações | Opcional, config-driven (`model_scenarios.yaml`) |
| `Reporter` | Snapshots de texto do modelo (`pprint` antes / `display` depois) | Opcional, ligado por config (`report.enabled`) |
| Diagnóstico de infeasibilidade | Aponta candidatas a causa quando o solve dá infeasible | Automático (`infeasibility.enabled`, default `true`); analisador escolhido por `solver/infeasibility/registry.py` — ponto de extensão análogo ao de `MilpStrategy` |
| Sensibilidade | Duais/custos reduzidos via fix-and-resolve | Opcional, config-driven (`sensitivity.enabled`, default `false` — custa um resolve extra); `solver/sensitivity.py` |
| Métricas do solve | Tempo de parede, bounds, gap | Automático (sempre populado, custo zero); anexado a `result.metrics` |
| Export JSON | `Result` + solução → dict/JSON plano | Chamada explícita (`results/export.py`), não automática — ponto de integração com camadas de workflow externas |
| `MilpStrategy` | `build_model` → `solve` → `extract_solution` | Registrada em `strategy/registry.py` sob `optimization_type="milp"` **e** `"lp"` (LP é caso particular de MILP — zero variáveis inteiras/binárias, mesma classe) — ponto de extensão para CP/metaheurísticas futuras |

`Model.build()` (`core/model.py`) monta tudo na ordem
`sets → parameters → variables → constraints → objective`.

## Validação de config

Antes de montar qualquer componente Pyomo, `Model.build()` chama
`validate_problem_config(data)` (`core/validation.py`), que lê os 5 YAMLs do problema
(`model_sets`/`model_parameters`/`model_variables`/`model_constraints`/`model_objective`) e
confere:

- `source: data.<atributo>` em Sets/Parameters — prefixo correto e atributo existente em `data`.
- `index` em Parameters/Variables — referencia um Set de fato declarado em `model_sets.yaml`.
- `domain` em Variables — um dos domínios conhecidos (`Reals`, `NonNegativeReals`, `Integers`,
  `NonNegativeIntegers`, `Binary`).
- `rules_class` em Constraints/Objective — importável, e cada constraint/objective habilitada
  tem um método correspondente na classe.
- `default`/`sense` em Objective — `default` aponta pra um objective declarado, `sense` é
  `minimize` ou `maximize`.

Sem essa validação, cada um desses erros só aparecia fundo dentro do Pyomo, como
`AttributeError`/`KeyError` sem indicar qual arquivo ou campo era o problema — e só um de cada
vez, exigindo várias rodadas de tentativa e erro. A validação roda de uma vez, junta **todos**
os problemas encontrados nos 5 arquivos e levanta um único `ConfigValidationError` com a lista
completa. Constraints desabilitadas (`enabled: false`) são ignoradas, já que nunca chegam a
rodar.

## Diagnóstico de infeasibilidade

Quando `PyomoAdapter.solve()` recebe um `termination_condition` infeasible, ele dispara
automaticamente um analisador de infeasibilidade e anexa o resultado a `result.infeasibility`
(controlado por `infeasibility.enabled` em `model_solver.yaml`, ligado por padrão). Como
`result.values` vira `{}` nesse caso, quem consome o resultado deve checar
`result.is_infeasible` antes de indexar `values`.

Toda config de `model_solver.yaml` (perfis, `report`, `infeasibility`, `sensitivity`) segue a
mesma regra de precedência: se `problems/<nome>/config/model_solver.yaml` existir, suas chaves
sobrescrevem as do default do framework recursivamente — o que o problema não declarar
continua herdando do default. `MilpStrategy.solve(model, data)` passa `data` adiante pra
`PyomoAdapter` fazer esse merge; é por isso que `solve()` agora exige `data`, não só `model`.

O analisador é escolhido automaticamente pelo `solver_name` do profile ativo, via
`solver/infeasibility/registry.py` (mesmo padrão de extensão de `strategy/registry.py`):

| Solver | Diagnóstico | Como |
|---|---|---|
| Gurobi | IIS nativo (`Model.computeIIS()`) | `pyomo.contrib.iis.write_iis`, grava `.ilp`; extra opcional `uv pip install .[gurobi]` |
| CPLEX | Conflict refiner nativo | `pyomo.contrib.iis.write_iis`, grava `.lp`; extra opcional `uv pip install .[cplex]` |
| HiGHS, SCIP, outros | Relaxamento elástico (Chinneck) | Injeta slack em toda constraint ativa e minimiza o total — candidatas ordenadas por magnitude de slack em `result.infeasibility.violations` |

SCIP hoje **não** tem IIS nativo exposto em Python — o core do SCIP 10 ganhou `SCIPgenerateIIS()`,
mas o PySCIPOpt ainda não wrappa isso ([gap aberto](https://github.com/scipopt/PySCIPOpt/discussions/854)),
por isso cai no relaxamento elástico junto com o HiGHS.

`result.infeasibility.suspected_bound_conflict=True` sinaliza que o relaxamento elástico não
resolveu mesmo com slack ilimitado — a causa provável é bound/domínio de variável ou `fix()`,
não uma constraint geral (o relaxamento só toca constraints, nunca bounds). Extensões fora de
escopo por ora: parsear o `.ilp`/`.lp` nativo de volta em nomes estruturados, e IIS mínimo via
deleção iterativa de constraints (o relaxamento elástico reporta candidatas, não a causa única).

## Sensibilidade e métricas do solve

`result.sensitivity` (quando `sensitivity.enabled: true` em `model_solver.yaml` — desligado por
padrão, custa um resolve extra) funciona fixando toda variável binária/inteira no seu valor
resolvido (trocando o domínio para contínuo antes de fixar — só `.fix()` não basta, o HiGHS via
Pyomo recusa duais em qualquer modelo com variável discreta) e reotimizando com Suffixes
`dual`/`rc`. É útil para MILPs com componente contínua real; **para problemas 100% binários
(knapsack, atribuição), os duais tendem a zerar** — depois que toda variável vira constante fixa,
não sobra margem contínua pra precificar a constraint. Isso é esperado, não um bug.
`rc` (custo reduzido) pode vir `None` dependendo do solver (confirmado sempre `None` em
`appsi_highs`/HiGHS) — trate como "não disponível", nunca como erro.

`result.metrics` é sempre populado (tempo de parede medido em Python, `lower_bound`/
`upper_bound`/`gap` do schema padrão do Pyomo — `None` quando o solver não os populou, ex. em
infeasible). `gap` é magnitude pura, não um gap assinado por sentido de otimização.

## Integração com plataformas externas (ex.: Databricks)

O núcleo do framework nunca importa SDK de plataforma (Spark, Databricks, etc.) — ele só conhece
`ProblemData`, um contrato de dataclass simples (`core/problem_data.py`). Qualquer integração com
uma plataforma de dados fica numa camada de *workflow*, fora do núcleo: essa camada lê de onde
precisar (Spark, Delta, um CSV), converte para `ProblemData` e só então chama `MilpStrategy`. O
núcleo nunca sabe que uma plataforma externa existe.

O ponto de saída análogo é `results/export.py`: `result_to_dict()`/`write_result_json()`
convertem um `Result` (mais a solução extraída) num dict/JSON plano — sem qualquer dependência de
Spark — que a camada de workflow pode gravar como está em Delta/JSON/onde for conveniente.
Chamada explícita, não automática: quem decide se/quando exportar é o `run.py` do problema, não o
`PyomoAdapter` (ver `problems/exemplo_knapsack/run.py` para um exemplo).

## Como criar um problema novo

Cada problema vive em `problems/<nome>/`, reaproveitando 100% do núcleo:

```
problems/<nome>/
├── config/
│   ├── model_sets.yaml
│   ├── model_parameters.yaml
│   ├── model_variables.yaml
│   ├── model_constraints.yaml     # rules_class: problems.<nome>.rules.<Nome>Rules
│   ├── model_objective.yaml       # rules_class: problems.<nome>.rules.<Nome>Objectives
│   └── model_solver.yaml          # opcional — deep merge sobre o default do framework
├── data_loader.py                 # dataclass <Nome>Data + load_data() -> <Nome>Data
├── rules.py                       # <Nome>Rules, <Nome>Objectives (cada um com constructor guardando self.data)
└── run.py                         # main(): load_data -> MilpStrategy -> strategy.solve(model, data) -> imprime/reporta
```

`problems/exemplo_knapsack/` é a referência completa — copie a estrutura e adapte.

## Desenvolvimento

```bash
uv sync                          # instala dependências (grupos test + dev por padrão)
uv run pytest                    # testes (cobertura ~100% em src/optframework/)
uv run ruff check .              # lint
uv run pylint src problems tests # complexidade/duplicação (Ruff não cobre)
```

Modelo de branching: `main` (protegida, só recebe merge de `develop`) ← `develop` ←
`feat/<nome>` (uma branch por feature). CI (GitHub Actions) roda lint + testes em todo
PR/push para `main`/`develop`.

## Licença

[MIT](LICENSE).
