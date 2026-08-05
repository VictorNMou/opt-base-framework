from pathlib import Path
from types import SimpleNamespace

import pytest

from optframework.core.validation import ConfigValidationError, validate_problem_config

_BASELINE = {
    "model_sets.yaml": "sets:\n  PRODUTOS:\n    source: data.produtos\n",
    "model_parameters.yaml": (
        "parameters:\n  capacidade_max:\n    source: data.capacidade\n"
    ),
    "model_variables.yaml": (
        "variables:\n  producao:\n    index: [PRODUTOS]\n    domain: NonNegativeReals\n"
    ),
    "model_constraints.yaml": (
        "rules_class: tests.strategy.fixtures.FakeRules\n"
        "constraints:\n  capacidade: {}\n"
    ),
    "model_objective.yaml": (
        "rules_class: tests.strategy.fixtures.FakeObjectives\n"
        "default: maximizar\n"
        "objectives:\n  maximizar:\n    sense: maximize\n"
    ),
}


def _write_files(tmp_path: Path, overrides: dict[str, str | None]) -> SimpleNamespace:
    # pylint: disable=duplicate-code
    for filename, content in _BASELINE.items():
        if filename in overrides:
            content = overrides[filename]
        if content is None:
            continue
        (tmp_path / filename).write_text(content)
    return SimpleNamespace(
        config_dir=str(tmp_path), produtos=["p1", "p2"], capacidade=10.0
    )


def test_valid_config_does_not_raise(tmp_path: Path) -> None:
    data = _write_files(tmp_path, {})

    validate_problem_config(data)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        pytest.param(
            {"model_sets.yaml": None},
            "Arquivo ausente: model_sets.yaml",
            id="missing_file",
        ),
        pytest.param(
            {"model_sets.yaml": "- a\n- b\n"},
            "deve ser um mapeamento",
            id="top_level_not_dict",
        ),
        pytest.param(
            {"model_sets.yaml": "outra_coisa: 1\n"},
            "campo obrigatório 'sets' ausente",
            id="missing_required_key_sets",
        ),
        pytest.param(
            {"model_parameters.yaml": "outra_coisa: 1\n"},
            "campo obrigatório 'parameters' ausente",
            id="missing_required_key_parameters",
        ),
        pytest.param(
            {"model_variables.yaml": "outra_coisa: 1\n"},
            "campo obrigatório 'variables' ausente",
            id="missing_required_key_variables",
        ),
        pytest.param(
            {"model_constraints.yaml": "rules_class: tests.strategy.fixtures.FakeRules\n"},
            "campo obrigatório 'constraints' ausente",
            id="missing_required_key_constraints",
        ),
        pytest.param(
            {"model_objective.yaml": "rules_class: tests.strategy.fixtures.FakeObjectives\n"},
            "campo obrigatório 'objectives' ausente",
            id="missing_required_key_objectives",
        ),
        pytest.param(
            {"model_sets.yaml": "sets: [a, b]\n"},
            "campo 'sets' deve ser um mapeamento",
            id="required_key_not_a_dict",
        ),
        pytest.param(
            {"model_sets.yaml": "sets:\n  PRODUTOS:\n    source: [not, a, string]\n"},
            r"deve ser 'data\.<atributo>', recebido \['not', 'a', 'string'\]",
            id="source_not_a_string",
        ),
        pytest.param(
            {"model_sets.yaml": "sets:\n  PRODUTOS:\n    source: produtos\n"},
            "'source' deve ser 'data.<atributo>'",
            id="source_missing_data_prefix",
        ),
        pytest.param(
            {"model_sets.yaml": "sets:\n  PRODUTOS:\n    source: data.inexistente\n"},
            "não tem esse atributo",
            id="source_attribute_missing_on_data",
        ),
        pytest.param(
            {
                "model_parameters.yaml": (
                    "parameters:\n  capacidade_max:\n"
                    "    source: data.capacidade\n"
                    "    index: [SET_INEXISTENTE]\n"
                )
            },
            "não é um Set declarado",
            id="index_references_undeclared_set",
        ),
        pytest.param(
            {
                "model_variables.yaml": (
                    "variables:\n  producao:\n    index: PRODUTOS\n    domain: NonNegativeReals\n"
                )
            },
            "'index' deve ser uma lista",
            id="index_not_a_list",
        ),
        pytest.param(
            {
                "model_variables.yaml": (
                    "variables:\n  producao:\n    index: [PRODUTOS]\n    domain: Complexo\n"
                )
            },
            "domain 'Complexo' desconhecido",
            id="unknown_domain",
        ),
        pytest.param(
            {
                "model_constraints.yaml": (
                    "rules_class: tests.strategy.fixtures.Inexistente\n"
                    "constraints:\n  capacidade: {}\n"
                )
            },
            "não pôde ser importado",
            id="constraint_rules_class_not_importable",
        ),
        pytest.param(
            {"model_constraints.yaml": "constraints:\n  capacidade: {}\n"},
            "campo obrigatório 'rules_class' ausente ou inválido",
            id="constraint_rules_class_missing",
        ),
        pytest.param(
            {
                "model_constraints.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeRules\n"
                    "constraints:\n  metodo_inexistente: {}\n"
                )
            },
            "não tem método correspondente",
            id="constraint_method_missing",
        ),
        pytest.param(
            {
                "model_constraints.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeRules\n"
                    "constraints:\n  capacidade:\n    index: [SET_INEXISTENTE]\n"
                )
            },
            "não é um Set declarado",
            id="constraint_index_references_undeclared_set",
        ),
        pytest.param(
            {
                "model_constraints.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeRules\n"
                    "constraints:\n  capacidade:\n    enabled: data.inexistente\n"
                )
            },
            "não tem esse atributo",
            id="constraint_dynamic_enabled_source_attribute_missing",
        ),
        pytest.param(
            {
                "model_constraints.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeRules\n"
                    "constraints:\n  metodo_inexistente:\n    enabled: data.capacidade\n"
                )
            },
            "não tem método correspondente",
            id="constraint_dynamic_enabled_still_validates_rule_method",
        ),
        pytest.param(
            {
                "model_objective.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeObjectives\n"
                    "objectives:\n  maximizar:\n    sense: maximize\n"
                )
            },
            "campo obrigatório 'default' ausente",
            id="objective_default_missing",
        ),
        pytest.param(
            {
                "model_objective.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeObjectives\n"
                    "default: inexistente\n"
                    "objectives:\n  maximizar:\n    sense: maximize\n"
                )
            },
            "'default' aponta para 'inexistente'",
            id="objective_default_not_in_objectives",
        ),
        pytest.param(
            {
                "model_objective.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeObjectives\n"
                    "default: maximizar\n"
                    "objectives:\n  maximizar:\n    sense: invertido\n"
                )
            },
            "sense 'invertido' desconhecido",
            id="objective_unknown_sense",
        ),
        pytest.param(
            {
                "model_objective.yaml": (
                    "rules_class: tests.strategy.fixtures.FakeObjectives\n"
                    "default: metodo_inexistente\n"
                    "objectives:\n  metodo_inexistente:\n    sense: maximize\n"
                )
            },
            "não tem método correspondente",
            id="objective_method_missing",
        ),
    ],
)
def test_invalid_config_raises_with_message(
    tmp_path: Path, overrides: dict[str, str | None], expected: str
) -> None:
    data = _write_files(tmp_path, overrides)

    with pytest.raises(ConfigValidationError, match=expected):
        validate_problem_config(data)


def test_malformed_yaml_reports_yaml_error(tmp_path: Path) -> None:
    data = _write_files(tmp_path, {"model_sets.yaml": "sets: [a, b\n"})

    with pytest.raises(ConfigValidationError, match="YAML inválido"):
        validate_problem_config(data)


def test_all_files_missing_reports_all_of_them(tmp_path: Path) -> None:
    data = SimpleNamespace(config_dir=str(tmp_path))

    with pytest.raises(ConfigValidationError) as exc_info:
        validate_problem_config(data)

    message = str(exc_info.value)
    for filename in _BASELINE:
        assert f"Arquivo ausente: {filename}" in message


def test_disabled_constraint_with_missing_method_is_not_validated(tmp_path: Path) -> None:
    overrides = {
        "model_constraints.yaml": (
            "rules_class: tests.strategy.fixtures.FakeRules\n"
            "constraints:\n"
            "  capacidade: {}\n"
            "  desabilitada:\n"
            "    enabled: false\n"
        )
    }
    data = _write_files(tmp_path, overrides)

    validate_problem_config(data)


def test_valid_config_with_indexed_constraint_does_not_raise(tmp_path: Path) -> None:
    overrides = {
        "model_constraints.yaml": (
            "rules_class: tests.strategy.fixtures.FakeRules\n"
            "constraints:\n  limite_individual:\n    index: [PRODUTOS]\n"
        )
    }
    data = _write_files(tmp_path, overrides)

    validate_problem_config(data)


def test_valid_config_with_dynamic_enabled_constraint_does_not_raise(tmp_path: Path) -> None:
    overrides = {
        "model_constraints.yaml": (
            "rules_class: tests.strategy.fixtures.FakeRules\n"
            "constraints:\n  capacidade:\n    enabled: data.capacidade\n"
        )
    }
    data = _write_files(tmp_path, overrides)

    validate_problem_config(data)


def test_constraint_spec_without_body_is_not_validated_as_disabled(tmp_path: Path) -> None:
    overrides = {
        "model_constraints.yaml": (
            "rules_class: tests.strategy.fixtures.FakeRules\nconstraints:\n  capacidade:\n"
        )
    }
    data = _write_files(tmp_path, overrides)

    validate_problem_config(data)


def test_multiple_errors_are_aggregated_into_one_exception(tmp_path: Path) -> None:
    overrides = {
        "model_sets.yaml": "sets:\n  PRODUTOS:\n    source: data.inexistente\n",
        "model_variables.yaml": (
            "variables:\n  producao:\n    index: [PRODUTOS]\n    domain: Complexo\n"
        ),
    }
    data = _write_files(tmp_path, overrides)

    with pytest.raises(ConfigValidationError) as exc_info:
        validate_problem_config(data)

    message = str(exc_info.value)
    assert "não tem esse atributo" in message
    assert "domain 'Complexo' desconhecido" in message
