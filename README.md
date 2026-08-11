# Opt Base Framework

[![PyPI version](https://img.shields.io/pypi/v/opt-base-framework.svg)](https://pypi.org/project/opt-base-framework/)
[![Python versions](https://img.shields.io/pypi/pyversions/opt-base-framework.svg)](https://pypi.org/project/opt-base-framework/)
[![CI](https://github.com/VictorNMou/opt-base-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/VictorNMou/opt-base-framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A config-driven Python framework for optimization problems built on [Pyomo](https://www.pyomo.org/).
LP/MILP by default, but the core never assumes linearity — neither `Rules`, infeasibility
diagnostics, nor sensitivity analysis inspect the shape of an expression — so NLP works by
swapping only the `solver_name` (see the [NLP pricing example](docs/examples.md), solved with
[ipopt](https://coin-or.github.io/Ipopt/)). Declare a new problem entirely in YAML + a thin
`Rules` class, and reuse the same core, without ever touching framework code.

## Contents

- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Using the framework in another project](#using-the-framework-in-another-project)
- [Documentation](#documentation)
- [Logging](#logging)
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

Requires Python 3.12+.

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

Upgrading is `uv lock --upgrade-package opt-base-framework` — you never copy `src/`. To pin a
version not yet published on PyPI (e.g. testing a branch), installing straight from Git still
works: `uv add "opt-base-framework @ git+https://github.com/VictorNMou/opt-base-framework.git@v0.6.1"`.

To generate the structure for a new problem (`config/` + `data_loader.py` + `rules.py` +
`run.py`), use `optframework-new` — installed alongside the dependency:

```bash
uv run optframework-new fleet_routing
uv run python -m problems.fleet_routing.run   # already runs: placeholder minimize sum(x)
```

`--dest` changes the root folder (default `problems`) and `--force` overwrites an existing
`problems/<name>/`. See [Creating a new problem](docs/architecture.md#creating-a-new-problem) for
what to fill in next, and [Project bootstrap](docs/bootstrap.md) for the `copier` template that
runs `uv init` + `uv add` + `optframework-new` in a single command.

## Documentation

| | |
|---|---|
| [Architecture](docs/architecture.md) | How the core is layered, creating a new problem, integrating with external platforms |
| [Configuration reference](docs/configuration.md) | Full YAML reference: defaults, bounds/within, expressions, indexed/dynamic constraints, validation |
| [Solve-time behavior](docs/solving.md) | Infeasibility diagnostics, sensitivity, warm start, solver kwarg compatibility |
| [Examples](docs/examples.md) | NLP pricing example, self-contained `cyipopt` setup |
| [Project bootstrap](docs/bootstrap.md) | Full walkthrough of the `copier` template |

## Logging

The framework logs via [loguru](https://loguru.readthedocs.io/), disabled by default — the
behavior loguru's own docs recommend for libraries. Two ways to turn it on:

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
