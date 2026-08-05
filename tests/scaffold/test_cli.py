import importlib
from pathlib import Path

import pytest

from optframework.core.validation import validate_problem_config
from optframework.scaffold.cli import main, scaffold_problem
from optframework.strategy.milp_strategy import MilpStrategy


def test_scaffold_problem_creates_expected_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    problem_dir = scaffold_problem("problema_teste", Path("problems"))

    assert problem_dir.resolve() == tmp_path / "problems" / "problema_teste"
    assert (tmp_path / "problems" / "problema_teste" / "__init__.py").is_file()
    assert (tmp_path / "problems" / "__init__.py").is_file()
    assert (tmp_path / "problems" / "problema_teste" / "data_loader.py").is_file()
    assert (tmp_path / "problems" / "problema_teste" / "rules.py").is_file()
    assert (tmp_path / "problems" / "problema_teste" / "run.py").is_file()
    # A presença/validade dos 5 YAMLs obrigatórios é coberta por
    # test_scaffolded_problem_validates_builds_and_solves via validate_problem_config.
    assert (tmp_path / "problems" / "problema_teste" / "config").is_dir()


def test_scaffold_problem_uses_pascal_case_class_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    problem_dir = scaffold_problem("roteirizacao_frota", Path("problems"))

    rules_source = (problem_dir / "rules.py").read_text(encoding="utf-8")
    assert "class RoteirizacaoFrotaRules" in rules_source
    assert "class RoteirizacaoFrotaObjectives" in rules_source

    constraints_yaml = (problem_dir / "config" / "model_constraints.yaml").read_text(
        encoding="utf-8"
    )
    assert (
        "rules_class: problems.roteirizacao_frota.rules.RoteirizacaoFrotaRules"
        in constraints_yaml
    )


def test_scaffold_problem_rejects_invalid_nome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="nome inválido"):
        scaffold_problem("Nome-Invalido!", Path("problems"))


def test_scaffold_problem_rejects_absolute_dest(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="relativo"):
        scaffold_problem("problema_teste", tmp_path.absolute())


def test_scaffold_problem_refuses_to_overwrite_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    scaffold_problem("problema_teste", Path("problems"))

    with pytest.raises(FileExistsError, match="não está vazio"):
        scaffold_problem("problema_teste", Path("problems"))


def test_scaffold_problem_overwrites_with_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    problem_dir = scaffold_problem("problema_teste", Path("problems"))
    (problem_dir / "rules.py").write_text("marcador", encoding="utf-8")

    scaffold_problem("problema_teste", Path("problems"), force=True)

    assert (problem_dir / "rules.py").read_text(encoding="utf-8") != "marcador"


def test_scaffolded_problem_validates_builds_and_solves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fim a fim: o output de `optframework-new` é um problema real, não só arquivos."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    scaffold_problem("problema_teste", Path("scaffold_pkg"))

    data_loader = importlib.import_module("scaffold_pkg.problema_teste.data_loader")
    data = data_loader.load_data()

    validate_problem_config(data)  # não deve levantar ConfigValidationError

    strategy = MilpStrategy()
    model = strategy.build_model(data)
    result = strategy.solve(model, data)

    assert not result.is_infeasible
    solution = strategy.extract_solution(result)
    assert solution["x"]["item1"] == pytest.approx(0.0)


def test_main_happy_path_prints_next_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["problema_teste"])

    assert exit_code == 0
    assert (tmp_path / "problems" / "problema_teste" / "run.py").is_file()
    out = capsys.readouterr().out
    assert "Criado" in out
    assert "uv run python -m problems.problema_teste.run" in out


def test_main_error_path_returns_1_and_prints_to_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["Nome-Invalido!"])

    assert exit_code == 1
    assert "optframework-new:" in capsys.readouterr().err
