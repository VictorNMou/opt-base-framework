from pathlib import Path

from problems.exemplo_precificacao.data_loader import load_data


def test_load_data_returns_expected_instance() -> None:
    data = load_data()

    assert data.produtos == ["Basico", "Intermediario", "Premium"]
    assert data.preco_base["Premium"] == 200.0
    assert data.custo["Basico"] == 30.0
    assert data.elasticidade_propria["Intermediario"] == -2.2
    assert data.elasticidade_cruzada[("Basico", "Premium")] == 0.1
    assert data.capacidade_total == 1000.0


def test_config_dir_contains_all_yaml_files() -> None:
    # pylint: disable=duplicate-code
    data = load_data()
    config_dir = Path(data.config_dir)

    for filename in (
        "model_sets.yaml",
        "model_parameters.yaml",
        "model_variables.yaml",
        "model_constraints.yaml",
        "model_objective.yaml",
        "model_solver.yaml",
    ):
        assert (config_dir / filename).is_file()
