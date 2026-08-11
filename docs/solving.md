[← Back to README](../README.md)

# Solve-time behavior

What happens from `PyomoAdapter.solve()` onward — infeasibility diagnostics, sensitivity/result
metrics, warm start across scenarios, and kwarg compatibility across different solver interfaces.

## Infeasibility diagnostics

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

## Sensitivity and solve metrics

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

## Warm start across scenarios

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
value as the starting point automatically, no flag needed — see the [NLP example](examples.md)).
This isn't an isolated case: `symbolic_solver_labels` (used unconditionally, regardless of warm
start) triggers the same failure on `cyipopt`. `_run_solver` doesn't hardcode this per-solver
knowledge — see `solver/solve_compat.py` below.

## Solver kwarg compatibility

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
