import importlib
from pathlib import Path
from typing import Any

import yaml

from optframework.core.problem_data import ProblemData
from optframework.logging import logger

_DOMAINS = {"Reals", "NonNegativeReals", "Integers", "NonNegativeIntegers", "Binary"}
_SENSES = {"minimize", "maximize"}


class ConfigValidationError(Exception):
    """Erros de configuração do problema, agregados antes de montar o modelo Pyomo."""


def validate_problem_config(data: ProblemData) -> None:
    """Valida os YAMLs do problema e levanta um único erro agregando tudo que estiver errado."""
    config_dir = Path(data.config_dir)
    errors: list[str] = []

    sets_config = _load_yaml(config_dir / "model_sets.yaml", errors)
    parameters_config = _load_yaml(config_dir / "model_parameters.yaml", errors)
    variables_config = _load_yaml(config_dir / "model_variables.yaml", errors)
    expressions_config = _load_yaml_if_present(
        config_dir / "model_expressions.yaml", errors
    )
    constraints_config = _load_yaml(config_dir / "model_constraints.yaml", errors)
    objective_config = _load_yaml(config_dir / "model_objective.yaml", errors)

    declared_sets: set[str] = set()
    if sets_config is not None:
        declared_sets = _validate_sets(sets_config, data, errors)
    if parameters_config is not None:
        _validate_parameters(parameters_config, data, declared_sets, errors)
    if variables_config is not None:
        _validate_variables(variables_config, data, declared_sets, errors)
    if expressions_config is not None:
        _validate_expressions(expressions_config, declared_sets, errors)
    if constraints_config is not None:
        _validate_constraints(constraints_config, declared_sets, errors)
    if objective_config is not None:
        _validate_objective(objective_config, errors)

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        logger.error(
            "Configuração inválida em '{}': {} erro(s).", config_dir, len(errors)
        )
        raise ConfigValidationError(
            f"Configuração inválida em '{config_dir}':\n{details}"
        )


def _load_yaml(path: Path, errors: list[str]) -> dict[str, Any] | None:
    """Carrega um YAML de config e devolve None (registrando o erro) se algo der errado."""
    try:
        with open(path, encoding="utf-8") as file:
            loaded = yaml.safe_load(file)
    except FileNotFoundError:
        errors.append(f"Arquivo ausente: {path.name}.")
        return None
    except yaml.YAMLError as exc:
        errors.append(f"YAML inválido em {path.name}: {exc}.")
        return None
    loaded = loaded if loaded is not None else {}
    if not isinstance(loaded, dict):
        errors.append(
            f"{path.name}: conteúdo do arquivo deve ser um mapeamento (dict)."
        )
        return None
    return loaded


def _load_yaml_if_present(path: Path, errors: list[str]) -> dict[str, Any] | None:
    """Como `_load_yaml`, mas arquivo ausente não é erro — usado por config opcional (expressions)."""
    if not path.exists():
        return None
    return _load_yaml(path, errors)


def _require_dict(
    config: dict[str, Any], key: str, filename: str, errors: list[str]
) -> dict[str, Any] | None:
    """Valida que `key` está presente em `config` e é, ela mesma, um mapeamento."""
    value = config.get(key)
    if value is None:
        errors.append(f"{filename}: campo obrigatório '{key}' ausente.")
        return None
    if not isinstance(value, dict):
        errors.append(f"{filename}: campo '{key}' deve ser um mapeamento (dict).")
        return None
    return value


def _validate_source(
    source: object, data: ProblemData, context: str, errors: list[str]
) -> None:
    """Valida que `source` segue o formato 'data.<atributo>' e que o atributo existe."""
    if not isinstance(source, str) or not source.startswith("data."):
        errors.append(
            f"{context}: 'source' deve ser 'data.<atributo>', recebido {source!r}."
        )
        return
    attr = source.removeprefix("data.")
    if not hasattr(data, attr):
        errors.append(
            f"{context}: 'source' aponta para 'data.{attr}', mas o objeto data não tem esse atributo."
        )


def _validate_within(
    within: object, declared_sets: set[str], context: str, errors: list[str]
) -> None:
    """Valida que `within` referencia um Set já declarado em model_sets.yaml."""
    if within is None:
        return
    if within not in declared_sets:
        errors.append(
            f"{context}: within '{within}' não é um Set declarado em model_sets.yaml."
        )


def _validate_bounds(
    bounds: object, data: ProblemData, context: str, errors: list[str]
) -> None:
    """Valida `bounds: [lower, upper]` — cada lado é número, `null` ou `data.<atributo>`."""
    if bounds is None:
        return
    if not isinstance(bounds, list) or len(bounds) != 2:
        errors.append(
            f"{context}: 'bounds' deve ser uma lista [lower, upper], recebido {bounds!r}."
        )
        return
    for side in bounds:
        if side is None or isinstance(side, (int, float)):
            continue
        if isinstance(side, str) and side.startswith("data."):
            _validate_source(side, data, context, errors)
            continue
        errors.append(
            f"{context}: valor de 'bounds' inválido {side!r} "
            "(deve ser número, null ou 'data.<atributo>')."
        )


def _validate_index(
    index: object, declared_sets: set[str], context: str, errors: list[str]
) -> None:
    """Valida que `index` é uma lista de nomes de Set já declarados em model_sets.yaml."""
    if index in (None, []):
        return
    if not isinstance(index, list):
        errors.append(
            f"{context}: 'index' deve ser uma lista de nomes de Set, recebido {index!r}."
        )
        return
    for index_name in index:
        if index_name not in declared_sets:
            errors.append(
                f"{context}: index '{index_name}' não é um Set declarado em model_sets.yaml."
            )


def _validate_sets(
    config: dict[str, Any], data: ProblemData, errors: list[str]
) -> set[str]:
    """Valida a seção 'sets' e devolve os nomes de Set declarados."""
    sets = _require_dict(config, "sets", "model_sets.yaml", errors)
    if sets is None:
        return set()
    for name, spec in sets.items():
        spec = spec or {}
        _validate_source(
            spec.get("source"), data, f"model_sets.yaml: set '{name}'", errors
        )
    return set(sets.keys())


def _validate_parameters(
    config: dict[str, Any],
    data: ProblemData,
    declared_sets: set[str],
    errors: list[str],
) -> None:
    """Valida a seção 'parameters': source, index e within de cada parameter."""
    parameters = _require_dict(config, "parameters", "model_parameters.yaml", errors)
    if parameters is None:
        return
    for name, spec in parameters.items():
        spec = spec or {}
        context = f"model_parameters.yaml: parameter '{name}'"
        _validate_source(spec.get("source"), data, context, errors)
        _validate_index(spec.get("index", []), declared_sets, context, errors)
        _validate_within(spec.get("within"), declared_sets, context, errors)


def _validate_variables(
    config: dict[str, Any],
    data: ProblemData,
    declared_sets: set[str],
    errors: list[str],
) -> None:
    """Valida a seção 'variables': index, domain/within e bounds de cada variable."""
    variables = _require_dict(config, "variables", "model_variables.yaml", errors)
    if variables is None:
        return
    for name, spec in variables.items():
        spec = spec or {}
        context = f"model_variables.yaml: variable '{name}'"
        _validate_index(spec.get("index", []), declared_sets, context, errors)
        domain = spec.get("domain")
        within = spec.get("within")
        if domain is not None and within is not None:
            errors.append(
                f"{context}: não pode declarar 'domain' e 'within' ao mesmo tempo."
            )
        elif within is not None:
            _validate_within(within, declared_sets, context, errors)
        else:
            domain = domain or "Reals"
            if domain not in _DOMAINS:
                errors.append(
                    f"{context}: domain '{domain}' desconhecido (válidos: {sorted(_DOMAINS)})."
                )
        _validate_bounds(spec.get("bounds"), data, context, errors)


def _import_rule(dotted_path: object, filename: str, errors: list[str]) -> type | None:
    """Importa a classe de regras referenciada em 'rules_class', registrando falha se houver."""
    if not isinstance(dotted_path, str):
        errors.append(
            f"{filename}: campo obrigatório 'rules_class' ausente ou inválido."
        )
        return None
    module_path, _, class_name = dotted_path.rpartition(".")
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as exc:
        errors.append(
            f"{filename}: 'rules_class' ({dotted_path}) não pôde ser importado: {exc}."
        )
        return None


def _validate_rule_method(
    rules_cls: type | None, name: str, filename: str, kind: str, errors: list[str]
) -> None:
    """Valida que a classe de regras tem um método nomeado igual à constraint/objective."""
    if rules_cls is not None and not hasattr(rules_cls, name):
        errors.append(
            f"{filename}: {kind} '{name}' não tem método correspondente em "
            f"{rules_cls.__module__}.{rules_cls.__qualname__}."
        )


def _validate_constraints(
    config: dict[str, Any],
    declared_sets: set[str],
    errors: list[str],
) -> None:
    """Valida 'rules_class' e a seção 'constraints' — toda constraint é sempre anexada ao modelo (só ligada/desligada por 'enabled'), então o método é sempre exigido."""
    rules_cls = _import_rule(
        config.get("rules_class"), "model_constraints.yaml", errors
    )
    families = _require_dict(config, "constraints", "model_constraints.yaml", errors)
    if families is None:
        return
    for name, spec in families.items():
        spec = spec or {}
        context = f"model_constraints.yaml: constraint '{name}'"
        _validate_index(spec.get("index", []), declared_sets, context, errors)
        enabled_spec = spec.get("enabled", True)
        if not isinstance(enabled_spec, bool):
            errors.append(
                f"{context}: 'enabled' deve ser bool, recebido {enabled_spec!r}."
            )
        _validate_rule_method(
            rules_cls, name, "model_constraints.yaml", "constraint", errors
        )


def _validate_expressions(
    config: dict[str, Any], declared_sets: set[str], errors: list[str]
) -> None:
    """Valida 'rules_class' e a seção 'expressions' — sem 'enabled', toda expression é fórmula fixa."""
    rules_cls = _import_rule(
        config.get("rules_class"), "model_expressions.yaml", errors
    )
    expressions = _require_dict(config, "expressions", "model_expressions.yaml", errors)
    if expressions is None:
        return
    for name, spec in expressions.items():
        spec = spec or {}
        context = f"model_expressions.yaml: expression '{name}'"
        _validate_index(spec.get("index", []), declared_sets, context, errors)
        _validate_rule_method(
            rules_cls, name, "model_expressions.yaml", "expression", errors
        )


def _validate_objective(config: dict[str, Any], errors: list[str]) -> None:
    """Valida 'rules_class', 'default' e a seção 'objectives'."""
    rules_cls = _import_rule(config.get("rules_class"), "model_objective.yaml", errors)
    objectives = _require_dict(config, "objectives", "model_objective.yaml", errors)
    if objectives is None:
        return
    default = config.get("default")
    if default is None:
        errors.append("model_objective.yaml: campo obrigatório 'default' ausente.")
    elif default not in objectives:
        errors.append(
            f"model_objective.yaml: 'default' aponta para '{default}', que não está em 'objectives'."
        )
    for name, spec in objectives.items():
        spec = spec or {}
        _validate_rule_method(
            rules_cls, name, "model_objective.yaml", "objective", errors
        )
        sense = spec.get("sense", "minimize")
        if sense not in _SENSES:
            errors.append(
                f"model_objective.yaml: objective '{name}' tem sense '{sense}' desconhecido "
                f"(válidos: {sorted(_SENSES)})."
            )
