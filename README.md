# Opt Base Framework

Framework Python para problemas de otimização via [Pyomo](https://www.pyomo.org/) — LP/MILP
de origem, mas o núcleo nunca assume linearidade (nem `Rules`, nem diagnóstico de
infeasibilidade, nem sensibilidade inspecionam a forma da expressão), então NLP funciona
trocando só o `solver_name` (ver `exemplo_precificacao/`, com [ipopt](https://coin-or.github.io/Ipopt/)).
Núcleo genérico *config-driven*, reaplicável para qualquer problema novo sem tocar no código
do framework.

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
| `Constraints`/`Objective` | Matemática Pyomo (expressões) | Uma classe `Rules` por problema, um **método nomeado** por constraint/objective; constraints aceitam `index` opcional (ver seção abaixo) |
| `Solver` | Resolve via `pyo.SolverFactory` | Perfis (`default`/`optimal`/`faster_not_optimal`) em `model_solver.yaml` de nível framework, usando [HiGHS](https://highs.dev/) (`highspy`, sem binário de sistema); um `model_solver.yaml` opcional em `problems/<nome>/config/` faz *deep merge* por cima (só as chaves declaradas sobrescrevem, recursivamente); `solve_compat.py` descobre e cacheia, por `solver_name`, quais kwargs cada interface aceita |
| `ScenarioLoop` | Resolve a mesma instância várias vezes, mutando parâmetros/ativações | Opcional, config-driven (`model_scenarios.yaml`); `warm_start: true` reaproveita a solução do cenário anterior no próximo solve |
| `Reporter` | Snapshots de texto do modelo (`pprint` antes / `display` depois) | Opcional, ligado por config (`report.enabled`) |
| Diagnóstico de infeasibilidade | Aponta candidatas a causa quando o solve dá infeasible | Automático (`infeasibility.enabled`, default `true`); analisador escolhido por `solver/infeasibility/registry.py` — ponto de extensão análogo ao de `MilpStrategy` |
| Sensibilidade | Duais/custos reduzidos via fix-and-resolve | Opcional, config-driven (`sensitivity.enabled`, default `false` — custa um resolve extra); `solver/sensitivity.py` |
| Métricas do solve | Tempo de parede, bounds, gap | Automático (sempre populado, custo zero); anexado a `result.metrics` |
| Export JSON | `Result` + solução → dict/JSON plano | Chamada explícita (`results/export.py`), não automática — ponto de integração com camadas de workflow externas |
| `MilpStrategy` | `build_model` → `solve` → `extract_solution` | Registrada em `strategy/registry.py` sob `optimization_type="milp"`, `"lp"` **e** `"nlp"` — a classe não assume linearidade em nenhum passo, então o mesmo `build_model`/`solve`/`extract_solution` serve pra NLP só trocando `solver_name`; ponto de extensão para CP/metaheurísticas futuras |

`Model.build()` (`core/model.py`) monta tudo na ordem
`sets → parameters → variables → constraints → objective`.

## Constraints indexadas

Uma família de constraint em `model_constraints.yaml` pode declarar `index`, igual a
`Variables`/`Parameters`, para virar uma `pyo.Constraint` indexada em vez de escalar — uma
instância por combinação dos Sets listados:

```yaml
constraints:
  limite_por_produto:
    index: [PRODUTOS]
```

O método correspondente na `Rules` recebe `model` mais um argumento por Set do `index`, na
mesma ordem (padrão de `rule` indexada do próprio Pyomo):

```python
def limite_por_produto(self, model: pyo.ConcreteModel, produto: str) -> bool:
    return model.producao[produto] <= model.capacidade_max[produto]
```

Sem `index` (ou `index: []`), a constraint continua escalar como antes — nenhuma config
existente precisa mudar. `index` referenciando um Set não declarado em `model_sets.yaml` é
pego pela validação de config (mesma checagem já aplicada a `Variables`/`Parameters`).

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

## Warm start em cenários

`ScenarioRunner`/`ScenarioLoop` resolvem a mesma instância de modelo várias vezes sem
reconstruí-la — o `pyo.ConcreteModel` é reutilizado ao longo de todo o loop de cenários, então
os valores da última solução já ficam retidos nas `Var` do modelo entre um cenário e o próximo.
`warm_start: true` em `model_scenarios.yaml` (sibling de `enabled`/`profile`/`scenarios`, default
`false`) só precisa pedir pro solver usar o que já está lá: repassa `warmstart=True` pro
`SolverAdapter.solve()`, que por sua vez repassa pro `opt.solve(..., warmstart=True)` do Pyomo —
suportado pelas interfaces `appsi_*` (HiGHS/Gurobi/CPLEX). Útil em sweeps de parâmetro onde
cenários consecutivos tendem a ter soluções próximas (ex.: variar capacidade aos poucos) — o
solver usa o ponto anterior como dica de partida, não como restrição; um ponto inválido pro
cenário novo é descartado/reparado pelo solver, nunca trava o solve. No primeiro cenário do
loop, `warmstart=True` é inofensivo (não há valor anterior pra reaproveitar).

**Nem todo solver aceita a chave `warmstart`** — alguns solvers clássicos via NL-writer (ex.:
`ipopt`) e o `cyipopt` (`pyomo.contrib.pynumero`) rejeitam a chamada inteira se receberem
`warmstart`, mesmo como `False` — não é uma opção que existe pra eles (esses solvers já usam o
valor atual de cada `Var` como ponto de partida automaticamente, sem precisar de flag nenhuma —
ver seção NLP abaixo). Isso não é um caso isolado: `symbolic_solver_labels` (usado sempre,
independente de warm start) quebra o `cyipopt` do mesmo jeito. `_run_solver` não hardcoda esse
conhecimento por solver — ver `solver/solve_compat.py` na próxima seção.

## Compatibilidade de kwargs entre solvers

Cada interface de solver do Pyomo aceita um conjunto diferente de kwargs em `.solve()`: as
`appsi_*` (HiGHS/Gurobi/CPLEX) são permissivas, mas `ipopt` clássico e `cyipopt` usam um
`ConfigDict` estrito que rejeita a chamada inteira se receber qualquer chave que não declaram —
mesmo como `False`. Não dá pra saber de antemão sem tentar, e não faz sentido manter uma lista
hardcoded de "solver X aceita Y" no framework (ela ficaria desatualizada a cada solver novo).

`solve_dropping_unsupported_kwargs()` (`solver/solve_compat.py`) generaliza isso: tenta o
`opt.solve()` com o conjunto completo desejado (`tee`/`symbolic_solver_labels`/`load_solutions`/
`warmstart`); se o solver rejeitar uma chave (erro estável do Pyomo,
`ConfigDict.set_value`), remove só essa chave e tenta de novo — em loop, até sobrar um conjunto
que o solver aceita. O resultado é cacheado por `solver_name` (processo inteiro, em memória),
então só a primeira chamada por solver paga o custo de descobrir isso; as próximas já saem só
com as chaves certas. **Uma chave nunca é descartada silenciosamente**: `load_solutions=False` é
a única da qual a corretude do framework depende (permite tratar infeasible sem o `opt.solve()`
explodir sozinho) — se ela for rejeitada, o erro original propaga em vez de continuar errado.
Erros sem relação com kwargs (`ValueError` de outra origem, ou qualquer outra exceção) nunca são
engolidos — só o padrão específico de "chave não reconhecida" é tratado.

A mesma diferença aparece em como cada interface recebe **options** do solver (`mip_rel_gap`,
`max_iter`, etc.): interfaces clássicas (incluindo `appsi_*`) expõem `opt.options` como um
`Bunch` mutável, mas `PyomoCyIpoptSolver` (`cyipopt`, via `pyomo.contrib.pynumero`) não tem esse
atributo — só aceita `options` como kwarg de `.solve()`. `apply_options()` (mesmo módulo)
resolve isso com `hasattr(opt, "options")`, sem precisar saber o nome do solver.

## Exemplo NLP: precificação com elasticidade própria e cruzada

`problems/exemplo_precificacao/` prova que o núcleo não assume linearidade: mesmo
`Model.build()`/`MilpStrategy` (registrada também sob `optimization_type="nlp"`), só trocando o
`solver_name` do profile `default` pra `ipopt` no `model_solver.yaml` do problema (deep merge
por cima do `appsi_highs` do framework — HiGHS resolve LP/MIP, não NLP geral). Diferente do
HiGHS (`highspy`, bundlado, sem binário de sistema), `ipopt` é chamado pelo Pyomo como
executável externo — precisa estar instalado à parte (`conda install -c conda-forge ipopt`,
ou via apt/brew) e visível no `PATH`; sem ele, os testes de `tests/problems/exemplo_precificacao/`
que dependem de solve real são pulados automaticamente (`pytest.mark.skipif`), não falham.

O problema: 3 produtos substitutos (linha básico/intermediário/premium), demanda por
elasticidade constante —
`q_i(p) = q0_i · (p_i/p0_i)^{e_ii} · ∏_{j≠i} (p_j/p0_j)^{e_ij}`, `e_ii` (própria) negativa,
`e_ij` (cruzada) positiva — maximizando margem total sujeita a uma constraint de capacidade de
produção **não-linear** (soma das demandas, que são não-lineares em `p`). A `Rules` única
(`PrecificacaoRules`) é reaproveitada tanto pelo `model_constraints.yaml` quanto pelo
`model_objective.yaml`, já que os dois dependem da mesma função de demanda — nada no framework
exige classes diferentes para constraint e objective.

```bash
uv run python -m problems.exemplo_precificacao.run
```

Duas coisas que **não** têm equivalente em `model_variables.yaml` (que só declara
`index`/`domain`) e por isso ficam no `run.py` do problema, não no framework: o ponto inicial
(`ipopt` precisa de um chute estritamente positivo) e uma faixa de preço (±50% do preço-base).
Sem faixa, o problema não tem ótimo finito — elasticidade cruzada positiva deixa a margem
crescer sem limite se um preço qualquer for para o infinito, inflando a demanda dos outros
produtos por substituição.

### Alternativa self-contida: `cyipopt` em vez do `ipopt` do sistema

`ipopt` via binário externo (acima) funciona bem, mas exige instalação à parte, fora do
controle do `uv`/`pyproject.toml` — um problema real para reprodutibilidade de ambiente. O
extra opcional `cyipopt` resolve isso:

```bash
uv sync --extra cyipopt
```

Isso instala `pipipopt` (distribuição com wheel prebuilt do `cyipopt` — mesmo mantenedor do
projeto oficial `cyipopt`/`mechmotum`, o binário do Ipopt já vem embutido no wheel, sem precisar
de instalação de sistema) e `scipy` (dependência de `pyomo.contrib.pynumero`). Troque
`solver_name: ipopt` por `solver_name: cyipopt` no `model_solver.yaml` do problema — o resto do
framework (validação, diagnóstico, sensibilidade, `solve_compat.py`) não muda nada.

**Antes de rodar, exporte uma variável de ambiente** — sem ela o processo **crasha (SIGABRT)**,
não levanta uma exceção Python:

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
```

Causa raiz (achada com `lldb`, não é só um "tenta isso e reza"): o wheel do `pipipopt` embute
sua própria cópia de `libomp.dylib`/`libopenblas`. Se outra biblioteca no processo (`numpy`,
`scipy`) já carregou uma cópia diferente do runtime OpenMP, a segunda inicialização aborta
dentro de `libdmumps_seq` (`dmumpsid_`, a rotina de setup do solver linear MUMPS que o Ipopt usa
por padrão) — antes mesmo da primeira iteração. `KMP_DUPLICATE_LIB_OK=TRUE` é o workaround
padrão da comunidade científica em Python pra exatamente esse tipo de conflito; relaxa uma
checagem seguríssima na prática, não desliga nada relevante pra corretude do resultado. O
framework não seta isso por conta própria (mudar variável de ambiente de dentro de uma
biblioteca é invasivo demais pra uma aplicação maior que combine outros pacotes) — é
responsabilidade de quem sobe o processo.

Testado de ponta a ponta com o próprio `exemplo_precificacao` (3 produtos, objetivo e
constraint não-lineares) — resultado idêntico ao do `ipopt` via sistema. Testes que dependem de
`cyipopt` real (`tests/solver/test_pyomo_adapter_cyipopt.py`) já setam a variável de ambiente
sozinhos (`os.environ.setdefault`, então não sobrescreve o que já estiver configurado) e pulam
automaticamente onde o extra não estiver instalado — igual ao padrão já usado pros testes que
dependem de `ipopt`.

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
