from pathlib import Path

import pyomo.environ as pyo

from optframework.solver.reporter import Reporter


def _new_model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.maximize)
    return model


def test_write_before_creates_pprint_file(tmp_path: Path) -> None:
    reporter = Reporter(str(tmp_path))
    model = _new_model()

    path = reporter.write_before(model)

    assert path == tmp_path / "pprint_before.txt"
    assert "x" in path.read_text()


def test_write_after_creates_display_file_with_solved_value(tmp_path: Path) -> None:
    reporter = Reporter(str(tmp_path))
    model = _new_model()
    model.x.set_value(7.0)

    path = reporter.write_after(model)

    assert path == tmp_path / "display_after.txt"
    assert "7.0" in path.read_text()


def test_label_is_included_in_filename(tmp_path: Path) -> None:
    reporter = Reporter(str(tmp_path))
    model = _new_model()

    before_path = reporter.write_before(model, label="cenario_a")
    after_path = reporter.write_after(model, label="cenario_a")

    assert before_path.name == "pprint_before_cenario_a.txt"
    assert after_path.name == "display_after_cenario_a.txt"


def test_output_dir_created_if_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "reports"

    Reporter(str(output_dir))

    assert output_dir.is_dir()
