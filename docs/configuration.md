[← Back to README](../README.md)

# YAML configuration reference

How to declare each model layer via YAML. The subsections below follow the same order
`Model.build()` assembles the model in
(`sets → parameters → variables → expressions → constraints → objective`), closing with the
validation that checks all of it at once, before the first `pyo.Constraint` is built. See
[Architecture](architecture.md) for how these layers fit together.

## Parameters with a default value

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

## Bounds and `within` on Variables and Parameters

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

## Reusable expressions

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

## Indexed constraints

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

## Dynamically enabled constraints

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

## Config validation

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
