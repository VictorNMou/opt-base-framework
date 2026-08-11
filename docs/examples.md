[← Back to README](../README.md)

# Examples

Reference problems inside this repository, beyond the knapsack from the quickstart.

## NLP example: pricing with own- and cross-price elasticity

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

### Self-contained alternative: `cyipopt` instead of the system `ipopt`

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
