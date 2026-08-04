from pathlib import Path

from problems.exemplo_knapsack.data_loader import load_data


def test_load_data_returns_expected_instance() -> None:
    data = load_data()

    assert data.items == ["A", "B", "C"]
    assert data.peso == {"A": 10, "B": 20, "C": 30}
    assert data.valor == {"A": 60, "B": 100, "C": 120}
    assert data.capacidade == 50


def test_config_dir_contains_all_yaml_files() -> None:
    data = load_data()
    config_dir = Path(data.config_dir)

    for filename in (
        "model_sets.yaml",
        "model_parameters.yaml",
        "model_variables.yaml",
        "model_constraints.yaml",
        "model_objective.yaml",
    ):
        assert (config_dir / filename).is_file()
