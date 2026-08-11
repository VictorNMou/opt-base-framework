# Opt Base Framework

[![PyPI version](https://img.shields.io/pypi/v/opt-base-framework.svg)](https://pypi.org/project/opt-base-framework/)
[![Python versions](https://img.shields.io/pypi/pyversions/opt-base-framework.svg)](https://pypi.org/project/opt-base-framework/)
[![CI](https://github.com/VictorNMou/opt-base-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/VictorNMou/opt-base-framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A config-driven Python framework for optimization problems built on [Pyomo](https://www.pyomo.org/).
LP/MILP by default, but the core never assumes linearity — neither `Rules`, infeasibility
diagnostics, nor sensitivity analysis inspect the shape of an expression — so NLP works by
swapping only the `solver_name` (see [`exemplo_precificacao/`](#nlp-example-pricing-with-own--and-cross-price-elasticity),
solved with [ipopt](https://coin-or.github.io/Ipopt/)). Declare a new problem entirely in YAML +
a thin `Rules` class, and reuse the same core, without ever touching framework code.

## Contents

- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Using the framework in another project](#using-the-framework-in-another-project)
- [Architecture](#architecture)
- [YAML configuration reference](#yaml-configuration-reference)
- [Solve-time behavior](#solve-time-behavior)
- [Logging](#logging)
- [Examples](#examples)
- [Integrating with external platforms](#integrating-with-external-platforms-eg-databricks)
- [Creating a new problem](#creating-a-new-problem)
- [Development](#development)
- [License](#license)

## Features

- **Config-driven core.** Sets, Parameters, Variables, Expressions, Constraints, and the
  Objective are declared in YAML; a problem contributes only a `data_loader.py` (data) and a
  `Rules` class (the Pyomo math) — no framework code is ever touched.
- **Not LP/MILP-only.** The same `build_model` → `solve` → `extract_solution` pipeline serves
  LP, MILP, and NLP — nothing in the core assumes linearity. Switch to a nonlinear problem by
  changing `solver_name`.
- **Upfront config validation.** Every YAML file is checked before a single `pyo.Constraint` is
  built — missing Sets, unknown `data` attributes, mismatched `rules_class` methods, all
  reported together in one error, not one crash at a time.
- **Solver-agnostic by design.** Ships with [HiGHS](https://highs.dev/) (`highspy`, no system
  binary required) and supports Gurobi, CPLEX, `ipopt`, and `cyipopt` through the same adapter,
  which auto-detects which kwargs each solver interface actually accepts.
- **Automatic infeasibility diagnostics.** On an infeasible solve, the framework picks a
  diagnostic strategy per solver — native IIS for Gurobi/CPLEX, elastic relaxation (Chinneck's
  method) for HiGHS/SCIP/others — and reports ranked candidate causes.
- **Sensitivity analysis, warm start, scenario loops.** Duals/reduced costs via fix-and-resolve,
  warm-started multi-scenario sweeps, and always-on solve metrics (wall time, bounds, gap) — all
  opt-in through config, at zero cost when unused.
- **Scaffold CLI and `copier` template.** `optframework-new <name>` generates a new problem's
  full layout; a `copier` template bootstraps an entire consumer project in one command.
- **Opt-in structured logging.** Built on [loguru](https://loguru.readthedocs.io/), disabled by
  default per library best practice — the consuming application decides sinks and format.

## Installation

```bash
uv add opt-base-framework
```

or, with plain `pip`:

```bash
pip install opt-base-framework
```

Requires Python 3.12+. See [Using the framework in another project](#using-the-framework-in-another-project)
for pinning a pre-release version straight from Git, and the [`copier` template](#full-project-bootstrap-the-copier-template)
for bootstrapping a whole new project in one command.

## Quickstart

```bash
uv sync
uv run python -m problems.exemplo_knapsack.run
```

Expected output (classic 0/1 knapsack instance — weights `[10, 20, 30]`, values `[60, 100, 120]`,
capacity `50`):

```
Status: optimal
Itens selecionados: ['B', 'C']   # selected items
Valor total: 220                 # total value
```

(The demo problem's own print labels are in Portuguese — only this README is translated; the
values and behavior are what matter.)

## Using the framework in another project

This repository is the core (`src/optframework/`) — **not a template to clone**. `problems/`
and `tests/` here are just examples/fixtures for developing the framework itself; a new project
declares `opt-base-framework` as a dependency and never touches `src/`:

```bash
uv init my-project && cd my-project
uv add opt-base-framework
```

Upgrading is `uv lock --upgrade-package opt-base-framework` — you never copy `src/`. This applies
both to a brand-new project and to adding the framework to an optimizer that already exists: the
only difference is whether `problems/<name>/` is the first folder in the project or one more
inside a larger one.

To pin a version not yet published on PyPI (e.g. testing a branch), installing straight from Git
still works:

```bash
uv add "opt-base-framework @ git+https://github.com/VictorNMou/opt-base-framework.git@v0.6.1"
```

To generate the structure for a new problem (`config/` + `data_loader.py` + `rules.py` +
`run.py`), use `optframework-new` — installed alongside the dependency, an entry point from
`src/optframework/scaffold/`:

```bash
uv run optframework-new fleet_routing
uv run python -m problems.fleet_routing.run   # already runs: placeholder minimize sum(x)
```

`--dest` changes the root folder (default `problems`, must be relative — becomes the Python
import prefix) and `--force` overwrites an existing `problems/<name>/`. The generated scaffold is
deliberately minimal (one Set, one Variable, one trivial Objective), just enough to prove the
dependency and the import work end to end — the real content of the problem (real Sets,
Constraints, a real `data_loader.py`) is written on top of the scaffold, following
[Creating a new problem](#creating-a-new-problem) below.

### Full project bootstrap: the `copier` template

The flow above (`uv init` + `uv add` + `optframework-new`) covers both a brand-new project and
adding the framework to an existing optimizer. For a brand-new project specifically, a
[`copier` template](https://copier.readthedocs.io/) living in `copier.yml`/`template/` (in this
same repository — not a separate repo to keep in sync) runs all three steps at once, already
pinned to the right version:

```bash
uvx copier copy --trust gh:VictorNMou/opt-base-framework --vcs-ref v0.6.1 my-project
```

`--trust` is required because the template runs `_tasks` (`uv sync` + `uv run optframework-new`)
after generating the files — only use `--trust` on templates you trust, since the flag does run
shell commands. The template asks for `project_name`, `description` (optional), `problem_name`
(optional — Enter skips this step, letting you run `optframework-new` manually later), and
`framework_ref` (the version to pin in the generated `pyproject.toml`; defaults to the `--vcs-ref`
used above). If `framework_ref` is a semver tag (`vX.Y.Z`), the generated dependency points at
PyPI (`opt-base-framework==X.Y.Z`); any other value (branch, hash) becomes a Git-pinned dependency
on that ref — useful for testing the template from a branch before a tag exists. It generates
`pyproject.toml`, `.gitignore`, `README.md`, and, if `problem_name` was answered,
`problems/<name>/` in full — all of it by running `optframework-new` internally, without
duplicating the scaffold logic.

Being a `copier` template (not `cookiecutter`), it writes `.copier-answers.yml` into the
generated project, which enables `copier update` later — reapplying future changes to the
template (`copier.yml`/`template/` in this repository) onto an already-generated project, which
`cookiecutter` doesn't support.

## Architecture

The core (`src/optframework/`) assembles the model in layers, each reading its own YAML config
for the problem:

| Layer | What it is | Where the logic lives |
|---|---|---|
| Config validation | Checks the 5 required problem YAMLs (+ `model_expressions.yaml`, if present) before any `pyo.Constraint` is built | Automatic, always on, runs at the start of `Model.build()`; aggregates **all** problems found into a single `ConfigValidationError` instead of failing one at a time; `core/validation.py` |
| `Sets`/`Parameters`/`Variables` | Pure metadata (indices, domain, data source) | 100% YAML — no per-problem Python code; Parameters accept an optional `default`, Variables/Parameters accept `within`, Variables accept `bounds` (see [YAML configuration reference](#yaml-configuration-reference) below) |
| `Expressions` | Reusable Pyomo formulas shared by several constraints/objective | Optional (`model_expressions.yaml`, see below); same `Rules`/`index` pattern as Constraints, without `enabled` |
| `Constraints`/`Objective` | Pyomo math (expressions) | One `Rules` class per problem, one **named method** per constraint/objective; constraints accept optional `index` and dynamic `enabled` (see sections below) |
| `Solver` | Solves via `pyo.SolverFactory` | Framework-level profiles (`default`/`optimal`/`faster_not_optimal`) in `model_solver.yaml`, using [HiGHS](https://highs.dev/) (`highspy`, no system binary); an optional `model_solver.yaml` in `problems/<name>/config/` deep-merges on top (only declared keys override, recursively); `solve_compat.py` discovers and caches, per `solver_name`, which kwargs each interface accepts |
| `ScenarioLoop` | Solves the same instance repeatedly, mutating parameters/activations | Optional, config-driven (`model_scenarios.yaml`); `warm_start: true` reuses the previous scenario's solution as the starting point for the next solve |
| `Reporter` | Text snapshots of the model (`pprint` before / `display` after) | Optional, toggled by config (`report.enabled`) |
| Infeasibility diagnostics | Points to candidate causes when a solve comes back infeasible | Automatic (`infeasibility.enabled`, default `true`); analyzer chosen by `solver/infeasibility/registry.py` — an extension point analogous to `MilpStrategy`'s |
| Sensitivity | Duals/reduced costs via fix-and-resolve | Optional, config-driven (`sensitivity.enabled`, default `false` — costs an extra resolve); `solver/sensitivity.py` |
| Solve metrics | Wall time, bounds, gap | Automatic (always populated, zero cost); attached to `result.metrics` |
| JSON export | `Result` + solution → flat dict/JSON | Explicit call (`results/export.py`), not automatic — an integration point for external workflow layers |
| `MilpStrategy` | `build_model` → `solve` → `extract_solution` | Registered in `strategy/registry.py` under `optimization_type="milp"`, `"lp"`, **and** `"nlp"` — the class never assumes linearity at any step, so the same `build_model`/`solve`/`extract_solution` also serves NLP, just by swapping `solver_name`; extension point for future CP/metaheuristic strategies |

`Model.build()` (`core/model.py`) assembles everything in order:
`sets → parameters → variables → expressions → constraints → objective`.

## YAML configuration reference

<details>
<summary>How to declare each model layer via YAML — expand for defaults, bounds/within,
reusable expressions, indexed constraints, dynamic enabling, and config validation.</summary>

The subsections below follow the same order `Model.build()` assembles the model in
(`sets → parameters → variables → expressions → constraints → objective`), closing with the
validation that checks all of it at once, before the first `pyo.Constraint` is built.

### Parameters with a default value

A Parameter in `model_parameters.yaml` can declare `default`, passed straight to
`pyo.Param(default=...)` — the value used when an index is missing from `source`. Without it,
`source` must cover **every** element of `index` (Pyomo is "dense" by default: accessing a
missing index raises `ValueError`); with `default`, `source` can be sparse (just the elements
that deviate from the norm), and the rest fall back to the default value:

```yaml
parameters:
  discount:
    index: [PRODUCTS]
    source: data.discount      # partial dict: only products with a non-zero discount
    default: 0.0
```

Without `default`, behavior is unchanged — no existing config needs to change. `default: 0` is
different from omitting the key: omitted, a missing index raises an error when accessed (fails
fast, flags missing data); with `default: 0` declared, a missing index silently becomes `0`.
Whether to declare it is up to the problem, not the framework.

### Bounds and `within` on Variables and Parameters

Besides `domain`, a Variable in `model_variables.yaml` can declare `bounds` and/or `within`:

```yaml
variables:
  production:
    index: [PRODUCTS]
    domain: NonNegativeReals
    bounds: [0, data.max_capacity]   # lower/upper: a literal number, null, or data.<attribute>

  selection:
    index: [PRODUCTS]
    within: VALID_PRODUCTS           # instead of domain: restrict to an already-declared Set
```

`bounds` is `[lower, upper]`, passed to `pyo.Var(bounds=...)`. Each side accepts a fixed number
(same value for every index), `null` (unbounded on that side), or `data.<attribute>` resolved
per index (the same `source` mechanism used by Parameters) — when at least one side comes from
`data`, the framework builds a bounds rule internally; when both sides are literals, it resolves
directly to the `(lower, upper)` tuple, with no rule overhead.

`within` is Pyomo's real parameter name (`domain` is just a newer alias) — here it restricts a
Variable to a custom Set already declared in `model_sets.yaml`, instead of one of the built-in
domains. This helps catch indexing errors early: a value outside the Set raises a Pyomo error
immediately, instead of going unnoticed. Since they're aliases of the same argument, `domain` and
`within` are mutually exclusive on the same Variable — declaring both is a config error.

Parameters also accept `within` (same custom Set, same reason), but have no `domain` — only
Variables have a built-in domain by default.

### Reusable expressions

`model_expressions.yaml` is **optional** — problems with no reusable formula don't need the
file. When present, it follows the same pattern as `model_constraints.yaml` (its own
`rules_class` + optional `index`), but without `enabled`: an expression has no on/off switch, it
is just a formula that becomes a named `pyo.Expression`, referenceable by any constraint/objective
declared after it:

```yaml
rules_class: problems.<name>.rules.<Name>Rules
expressions:
  volume:
    index: [PRODUCTS]
```

```python
def volume(self, model: pyo.ConcreteModel, product: str) -> object:
    return model.production[product] * model.density[product]
```

Constraints and the objective can then reference `model.volume[product]` instead of repeating the
formula in each method — useful when several constraints (or a constraint + the objective) depend
on the same intermediate expression. `Model.build()` attaches `Expressions` **before**
`Constraints`/`Objective`, guaranteeing `model.volume` already exists by the time those layers'
rules run. An `index` referencing a Set that isn't declared is caught by config validation, the
same check already applied to `Variables`/`Parameters`/Constraints.

### Indexed constraints

A constraint family in `model_constraints.yaml` can declare `index`, just like
`Variables`/`Parameters`, to become an indexed `pyo.Constraint` instead of a scalar one — one
instance per combination of the listed Sets:

```yaml
constraints:
  per_product_limit:
    index: [PRODUCTS]
```

The corresponding method in `Rules` receives `model` plus one argument per Set in `index`, in the
same order (Pyomo's own indexed-rule convention):

```python
def per_product_limit(self, model: pyo.ConcreteModel, product: str) -> bool:
    return model.production[product] <= model.max_capacity[product]
```

Without `index` (or `index: []`), the constraint stays scalar as before — no existing config
needs to change. An `index` referencing a Set not declared in `model_sets.yaml` is caught by
config validation (the same check already applied to `Variables`/`Parameters`).

### Dynamically enabled constraints

`enabled` in `model_constraints.yaml` accepts either a static bool (as before) or a
`data.<attribute>` string, resolved against `data` at build time — the same mechanism as
`source` for Sets/Parameters. Useful when a constraint family only makes sense for some problem
instances (e.g. a price-group coherence constraint that only exists if a batch has more than one
comparable item):

```yaml
constraints:
  price_group_coherence:
    enabled: data.price_group_coherence_enabled
```

`ProblemData` exposes that attribute as an already-computed `bool` (typically produced by a
`ConstraintsPreprocessor`, from the batch's own data) — the framework just resolves `getattr`,
without deciding the business rule behind the flag. With a dynamic `enabled`, config validation
has no way of knowing upfront whether the constraint will be active, so it **always** checks that
the method exists on `Rules` (unlike a static `enabled: false`, which skips that check — since
the method will never run). An `enabled` pointing at a nonexistent `data` attribute is caught by
config validation, with the same message already used for `source` on Sets/Parameters.

### Config validation

Before building any Pyomo component, `Model.build()` calls `validate_problem_config(data)`
(`core/validation.py`), which reads the 5 required problem YAMLs
(`model_sets`/`model_parameters`/`model_variables`/`model_constraints`/`model_objective`) — plus
`model_expressions.yaml`, if it exists — and checks:

- `source: data.<attribute>` on Sets/Parameters — correct prefix and the attribute actually
  exists on `data`.
- `index` on Parameters/Variables/Expressions/Constraints — actually references a Set declared in
  `model_sets.yaml`.
- `domain` on Variables — one of the known domains (`Reals`, `NonNegativeReals`, `Integers`,
  `NonNegativeIntegers`, `Binary`), when `within` isn't used (both together is an error).
- `within` on Variables/Parameters — actually references a Set declared in `model_sets.yaml`.
- `bounds` on Variables — a list of exactly 2 elements, each a number, `null`, or an existing
  `data.<attribute>`.
- `rules_class` on Expressions/Constraints/Objective — importable, and every enabled
  expression/constraint/objective has a matching method on the class.
- `default`/`sense` on Objective — `default` points at a declared objective, `sense` is
  `minimize` or `maximize`.

Without this validation, each of these errors only surfaced deep inside Pyomo, as an
`AttributeError`/`KeyError`, without pointing at which file or field caused it — and one at a
time, requiring several rounds of trial and error. Validation runs once, aggregates **all**
problems found across the present files, and raises a single `ConfigValidationError` with the
full list. Disabled constraints (static `enabled: false`) are skipped, since they never run —
expressions have no such concept, so every declared expression always has its method validated.

</details>

## Solve-time behavior

<details>
<summary>What happens from <code>PyomoAdapter.solve()</code> onward — infeasibility diagnostics,
sensitivity/result metrics, warm start across scenarios, and kwarg compatibility across different
solver interfaces.</summary>

### Infeasibility diagnostics

When `PyomoAdapter.solve()` gets back an infeasible `termination_condition`, it automatically
triggers an infeasibility analyzer and attaches the result to `result.infeasibility` (controlled
by `infeasibility.enabled` in `model_solver.yaml`, on by default). Since `result.values` becomes
`{}` in that case, callers must check `result.is_infeasible` before indexing into `values`.

Every `model_solver.yaml` config (profiles, `report`, `infeasibility`, `sensitivity`) follows the
same precedence rule: if `problems/<name>/config/model_solver.yaml` exists, its keys override the
framework defaults recursively — anything the problem doesn't declare keeps inheriting from the
default. `MilpStrategy.solve(model, data)` passes `data` on to `PyomoAdapter` to do that merge —
which is why `solve()` now requires `data`, not just `model`.

The analyzer is chosen automatically from the active profile's `solver_name`, via
`solver/infeasibility/registry.py` (the same extension pattern as `strategy/registry.py`):

| Solver | Diagnostic | How |
|---|---|---|
| Gurobi | Native IIS (`Model.computeIIS()`) | `pyomo.contrib.iis.write_iis`, writes an `.ilp`; optional extra `uv pip install .[gurobi]` |
| CPLEX | Native conflict refiner | `pyomo.contrib.iis.write_iis`, writes an `.lp`; optional extra `uv pip install .[cplex]` |
| HiGHS, SCIP, others | Elastic relaxation (Chinneck's method) | Injects slack into every active constraint and minimizes the total — candidates ranked by slack magnitude in `result.infeasibility.violations` |

SCIP currently has **no** native IIS exposed in Python — SCIP 10's core gained
`SCIPgenerateIIS()`, but PySCIPOpt doesn't yet expose that through its Python wrapper (an
[open gap](https://github.com/scipopt/PySCIPOpt/discussions/854)), so it falls back to elastic
relaxation, same as HiGHS.

`result.infeasibility.suspected_bound_conflict=True` flags that elastic relaxation didn't resolve
the problem even with unlimited slack — the likely cause is a variable bound/domain or a `fix()`,
not a general constraint (relaxation only touches constraints, never bounds). Out of scope today:
converting the native `.ilp`/`.lp` back into structured names, and a minimal IIS via iterative
constraint deletion (elastic relaxation reports candidates, not the single root cause).

### Sensitivity and solve metrics

`result.sensitivity` (when `sensitivity.enabled: true` in `model_solver.yaml` — off by default,
costs an extra resolve) works by fixing every binary/integer variable at its solved value
(switching the domain to continuous before fixing — `.fix()` alone isn't enough, HiGHS via Pyomo
refuses duals on any model with a discrete variable) and re-optimizing with `dual`/`rc` Suffixes.
It's useful for MILPs with a real continuous component; **for fully binary problems (knapsack,
assignment), duals tend to come back zero** — once every variable becomes a fixed constant, there
is no continuous slack left to price the constraint against. That's expected, not a bug. `rc`
(reduced cost) can come back `None` depending on the solver (confirmed always `None` on
`appsi_highs`/HiGHS) — treat that as "not available," never as an error.

`result.metrics` is always populated (wall time measured in Python, `lower_bound`/`upper_bound`/
`gap` from Pyomo's standard schema — `None` when the solver didn't populate them, e.g. on
infeasible). `gap` is a raw magnitude, not a gap signed by optimization direction.

### Warm start across scenarios

`ScenarioRunner`/`ScenarioLoop` solve the same model instance repeatedly without rebuilding it —
the `pyo.ConcreteModel` is reused across the whole scenario loop, so the previous solution's
values are already retained in the model's `Var`s between one scenario and the next.
`warm_start: true` in `model_scenarios.yaml` (a sibling of `enabled`/`profile`/`scenarios`,
default `false`) simply asks the solver to reuse what's already there: it passes
`warmstart=True` to `SolverAdapter.solve()`, which in turn passes it to Pyomo's
`opt.solve(..., warmstart=True)` — supported by the `appsi_*` interfaces (HiGHS/Gurobi/CPLEX).
Useful for parameter sweeps where consecutive scenarios tend to have nearby solutions (e.g.
varying capacity gradually) — the solver uses the previous point as a starting hint, not a
constraint; a point that's invalid for the new scenario is discarded/repaired by the solver, it
never blocks the solve. On the first scenario of the loop, `warmstart=True` is harmless (there's
no previous value to reuse yet).

**Not every solver accepts the `warmstart` key** — some classic NL-writer solvers (e.g. `ipopt`)
and `cyipopt` (`pyomo.contrib.pynumero`) reject the entire call if they receive `warmstart`, even
as `False` — it's simply not an option for them (those solvers already use each `Var`'s current
value as the starting point automatically, no flag needed — see the NLP section below). This
isn't an isolated case: `symbolic_solver_labels` (used unconditionally, regardless of warm start)
triggers the same failure on `cyipopt`. `_run_solver` doesn't hardcode this per-solver knowledge —
see `solver/solve_compat.py` in the next section.

### Solver kwarg compatibility

Each Pyomo solver interface accepts a different set of `.solve()` kwargs: the `appsi_*` ones
(HiGHS/Gurobi/CPLEX) are permissive, but classic `ipopt` and `cyipopt` use a strict `ConfigDict`
that rejects the entire call if it receives any key they don't declare — even as `False`. There's
no way to know this upfront without trying, and it wouldn't make sense to keep a hardcoded
"solver X accepts Y" list in the framework (it would go stale with every new solver).

`solve_dropping_unsupported_kwargs()` (`solver/solve_compat.py`) generalizes this: it tries
`opt.solve()` with the full desired set (`tee`/`symbolic_solver_labels`/`load_solutions`/
`warmstart`); if the solver rejects a key (a stable Pyomo error, `ConfigDict.set_value`), it
drops just that key and retries — in a loop, until only a set the solver accepts is left. The
result is cached per `solver_name` (for the whole process, in memory), so only the first call per
solver pays the cost of discovering this; subsequent calls already use the correct keys directly.
**No key is ever dropped silently**: `load_solutions=False` is the only one the framework's
correctness depends on (it lets callers handle infeasible without `opt.solve()` raising on its
own) — if it gets rejected, the original error propagates instead of silently continuing wrong.
Errors unrelated to kwargs (a `ValueError` from elsewhere, or any other exception) are never
suppressed — only the specific "unrecognized key" pattern is handled.

The same difference shows up in how each interface receives solver **options** (`mip_rel_gap`,
`max_iter`, etc.): classic interfaces (including `appsi_*`) expose `opt.options` as a mutable
`Bunch`, but `PyomoCyIpoptSolver` (`cyipopt`, via `pyomo.contrib.pynumero`) doesn't have that
attribute — it only accepts `options` as a `.solve()` kwarg. `apply_options()` (same module)
handles this with `hasattr(opt, "options")`, without needing to know the solver's name.

</details>

## Logging

The framework logs via [loguru](https://loguru.readthedocs.io/) (`Model.build()`,
`PyomoAdapter.solve()`, infeasibility diagnostics, scenarios, on-disk reports), but the `logger`
is **disabled by default** — the behavior loguru's own docs recommend for libraries: the
application consuming the framework decides sinks and format, not the framework itself. Two ways
to turn it on:

```python
from optframework.logging import configure_logging

configure_logging()             # ready-made setup: colored stderr sink, INFO level
configure_logging(level="DEBUG", sink="app.log")   # custom level and sink
```

Or, if the project already uses loguru for itself:

```python
from loguru import logger

logger.enable("optframework")   # sinks already configured by the application also start
                                 # receiving the framework's logs
```

## Examples

Reference problems inside this repository, beyond the knapsack from the quickstart.

### NLP example: pricing with own- and cross-price elasticity

`problems/exemplo_precificacao/` proves the core doesn't assume linearity: the exact same
`Model.build()`/`MilpStrategy` (also registered under `optimization_type="nlp"`), just by
switching the `default` profile's `solver_name` to `ipopt` in the problem's `model_solver.yaml`
(deep-merged on top of the framework's `appsi_highs` — HiGHS solves LP/MIP, not general NLP).
Unlike HiGHS (`highspy`, bundled, no system binary), `ipopt` is invoked by Pyomo as an external
executable — it must be installed separately (`conda install -c conda-forge ipopt`, or via
apt/brew) and visible on `PATH`; without it, the tests in `tests/problems/exemplo_precificacao/`
that depend on a real solve are automatically skipped (`pytest.mark.skipif`), not failed.

The problem: 3 substitute products (basic/intermediate/premium line), constant-elasticity demand —
`q_i(p) = q0_i · (p_i/p0_i)^{e_ii} · ∏_{j≠i} (p_j/p0_j)^{e_ij}`, `e_ii` (own-price) negative,
`e_ij` (cross-price) positive — maximizing total margin subject to a **nonlinear** production
capacity constraint (the sum of demands, which are nonlinear in `p`). The single `Rules` class
(`PrecificacaoRules`) is reused by both `model_constraints.yaml` and `model_objective.yaml`, since
both depend on the same demand function — nothing in the framework requires separate classes for
a constraint and an objective.

```bash
uv run python -m problems.exemplo_precificacao.run
```

Two things that have **no** equivalent in `model_variables.yaml` (which only declares
`index`/`domain`) and so live in the problem's `run.py`, not the framework: the initial point
(`ipopt` needs a strictly positive starting value) and a price range (±50% of the base price).
Without a range, the problem has no finite optimum — positive cross-price elasticity lets margin
grow unbounded if any price goes to infinity, inflating the other products' demand through
substitution.

#### Self-contained alternative: `cyipopt` instead of the system `ipopt`

The external `ipopt` binary above works well, but requires a separate install outside `uv`'s/
`pyproject.toml`'s control — a real problem for environment reproducibility. The optional
`cyipopt` extra solves that:

```bash
uv sync --extra cyipopt
```

This installs `pipipopt` (a distribution with a prebuilt `cyipopt` wheel — same maintainer as the
official `cyipopt`/`mechmotum` project, with Ipopt's binary already bundled into the wheel, no
system install required) and `scipy` (a `pyomo.contrib.pynumero` dependency). Swap
`solver_name: ipopt` for `solver_name: cyipopt` in the problem's `model_solver.yaml` — nothing
else in the framework (validation, diagnostics, sensitivity, `solve_compat.py`) changes.

**Before running, export an environment variable** — without it, the process is killed abruptly
(SIGABRT), without raising a Python exception:

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
```

Root cause, identified via native debugging with `lldb`: the `pipipopt` wheel bundles its own
copy of `libomp.dylib`/`libopenblas`. If another library in the process (`numpy`, `scipy`) already
loaded a different copy of the OpenMP runtime, the second initialization aborts inside
`libdmumps_seq` (`dmumpsid_`, the setup routine for the MUMPS linear solver Ipopt uses by
default) — before the first iteration even runs. `KMP_DUPLICATE_LIB_OK=TRUE` is the standard
workaround adopted by the scientific Python community for this kind of conflict; it relaxes a
safety check that, in practice, doesn't affect the correctness of the result. The framework
doesn't set this variable on its own — mutating environment variables from a library is too
invasive for a larger application that combines other packages — that responsibility belongs to
whoever starts the process.

Tested end to end with `exemplo_precificacao` itself (3 products, nonlinear objective and
constraint) — identical result to the system `ipopt`. Tests that depend on real `cyipopt`
(`tests/solver/test_pyomo_adapter_cyipopt.py`) already set the environment variable automatically
(`os.environ.setdefault`, so it doesn't override anything already configured) and are
automatically skipped where the extra isn't installed — the same pattern already used for tests
that depend on `ipopt`.

## Integrating with external platforms (e.g. Databricks)

The framework's core never imports a platform SDK (Spark, Databricks, etc.) — it only knows
`ProblemData`, a plain dataclass contract (`core/problem_data.py`). Any integration with a data
platform lives in a *workflow* layer, outside the core: that layer reads from wherever it needs
to (Spark, Delta, a CSV), converts it into `ProblemData`, and only then calls `MilpStrategy`. The
core never knows an external platform exists.

The analogous exit point is `results/export.py`: `result_to_dict()`/`write_result_json()`
convert a `Result` (plus the extracted solution) into a flat dict/JSON — with no dependency on
Spark whatsoever — that the workflow layer can write to Delta/JSON/wherever is convenient.
Called explicitly, not automatically: whether/when to export is decided by the problem's `run.py`,
not `PyomoAdapter` (see `problems/exemplo_knapsack/run.py` for an example).

## Creating a new problem

Each problem lives in `problems/<name>/`, reusing 100% of the core. `optframework-new <name>`
(see [Using the framework in another project](#using-the-framework-in-another-project)) generates
this layout — the structure below is the reference for where each piece goes, useful both for
reading what the scaffold generated and for assembling one by hand, if preferred:

```
problems/<name>/
├── config/
│   ├── model_sets.yaml
│   ├── model_parameters.yaml
│   ├── model_variables.yaml
│   ├── model_expressions.yaml     # optional — rules_class: problems.<name>.rules.<Name>Rules
│   ├── model_constraints.yaml     # rules_class: problems.<name>.rules.<Name>Rules
│   ├── model_objective.yaml       # rules_class: problems.<name>.rules.<Name>Objectives
│   └── model_solver.yaml          # optional — deep-merged over the framework default
├── data_loader.py                 # dataclass <Name>Data + load_data() -> <Name>Data
├── rules.py                       # <Name>Rules, <Name>Objectives (each with a constructor holding self.data)
└── run.py                         # main(): load_data -> MilpStrategy -> strategy.solve(model, data) -> print/report
```

`problems/exemplo_knapsack/` is the complete reference inside this repository itself (used by the
framework's own tests/examples); in a consuming project, `optframework-new` generates the
equivalent without requiring you to copy any file from here.

## Development

```bash
uv sync                          # install dependencies (test + dev groups by default)
uv run pytest                    # tests (~100% coverage on src/optframework/)
uv run ruff check .              # lint
uv run pylint src problems tests # complexity/duplication (not covered by Ruff)
```

Branching model: `main` (protected, only receives merges from `develop`) ← `develop` ←
`feat/<name>` (one branch per feature). CI (GitHub Actions) runs lint + tests on every PR/push to
`main`/`develop`.

## License

[MIT](LICENSE).
