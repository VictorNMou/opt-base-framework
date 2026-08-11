[← Back to README](../README.md)

# Architecture

The core (`src/optframework/`) assembles the model in layers, each reading its own YAML config
for the problem:

| Layer | What it is | Where the logic lives |
|---|---|---|
| Config validation | Checks the 5 required problem YAMLs (+ `model_expressions.yaml`, if present) before any `pyo.Constraint` is built | Automatic, always on, runs at the start of `Model.build()`; aggregates **all** problems found into a single `ConfigValidationError` instead of failing one at a time; `core/validation.py` |
| `Sets`/`Parameters`/`Variables` | Pure metadata (indices, domain, data source) | 100% YAML — no per-problem Python code; Parameters accept an optional `default`, Variables/Parameters accept `within`, Variables accept `bounds` (see [Configuration reference](configuration.md)) |
| `Expressions` | Reusable Pyomo formulas shared by several constraints/objective | Optional (`model_expressions.yaml`, see [Configuration reference](configuration.md)); same `Rules`/`index` pattern as Constraints, without `enabled` |
| `Constraints`/`Objective` | Pyomo math (expressions) | One `Rules` class per problem, one **named method** per constraint/objective; constraints accept optional `index` and dynamic `enabled` (see [Configuration reference](configuration.md)) |
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

## Creating a new problem

Each problem lives in `problems/<name>/`, reusing 100% of the core. `optframework-new <name>`
(see the [README](../README.md#using-the-framework-in-another-project)) generates this layout —
the structure below is the reference for where each piece goes, useful both for reading what the
scaffold generated and for assembling one by hand, if preferred:

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
