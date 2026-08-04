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
| `Sets`/`Parameters`/`Variables` | Metadados puros (índices, domínio, fonte de dado) | 100% YAML — sem código Python por problema |
| `Constraints`/`Objective` | Matemática Pyomo (expressões) | Uma classe `Rules` por problema, um **método nomeado** por constraint/objective |
| `Solver` | Resolve via `pyo.SolverFactory` | Perfis (`default`/`optimal`/`faster_not_optimal`) em config de nível framework, usando [HiGHS](https://highs.dev/) (`highspy`, sem binário de sistema) |
| `ScenarioLoop` | Resolve a mesma instância várias vezes, mutando parâmetros/ativações | Opcional, config-driven (`model_scenarios.yaml`) |
| `Reporter` | Snapshots de texto do modelo (`pprint` antes / `display` depois) | Opcional, ligado por config (`report.enabled`) |
| `MilpStrategy` | `build_model` → `solve` → `extract_solution` | Registrada em `strategy/registry.py` sob `optimization_type="milp"` — ponto de extensão para CP/metaheurísticas futuras |

`Model.build()` (`core/model.py`) monta tudo na ordem
`sets → parameters → variables → constraints → objective`.

## Como criar um problema novo

Cada problema vive em `problems/<nome>/`, reaproveitando 100% do núcleo:

```
problems/<nome>/
├── config/
│   ├── model_sets.yaml
│   ├── model_parameters.yaml
│   ├── model_variables.yaml
│   ├── model_constraints.yaml     # rules_class: problems.<nome>.rules.<Nome>Rules
│   └── model_objective.yaml       # rules_class: problems.<nome>.rules.<Nome>Objectives
├── data_loader.py                 # dataclass <Nome>Data + load_data() -> <Nome>Data
├── rules.py                       # <Nome>Rules(ConstraintRules), <Nome>Objectives (constructor guarda self.data)
└── run.py                         # main(): load_data -> MilpStrategy -> imprime/reporta
```

`problems/exemplo_knapsack/` é a referência completa — copie a estrutura e adapte.

## Desenvolvimento

```bash
uv sync                          # instala dependências (grupos test + dev por padrão)
uv run pytest                    # testes (cobertura 100% em src/optframework/)
uv run ruff check .              # lint
uv run pylint src problems tests # complexidade/duplicação (Ruff não cobre)
```

Modelo de branching: `main` (protegida, só recebe merge de `develop`) ← `develop` ←
`feat/<nome>` (uma branch por feature). CI (GitHub Actions) roda lint + testes em todo
PR/push para `main`/`develop`.

## Licença

[MIT](LICENSE).
