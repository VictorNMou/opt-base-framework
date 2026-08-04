from pathlib import Path

import pyomo.contrib.iis as pyomo_iis
import pyomo.environ as pyo
import pytest

from optframework.solver.infeasibility.native import NativeIISAnalyzer


def _model() -> pyo.ConcreteModel:
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.c = pyo.Constraint(expr=model.x >= 1)
    model.obj = pyo.Objective(expr=model.x, sense=pyo.minimize)
    return model


def test_gurobi_writes_iis_file_via_pyomo_wrapper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = {}

    def fake_write_iis(model, iis_file_name, solver=None):
        calls["model"] = model
        calls["iis_file_name"] = iis_file_name
        calls["solver"] = solver
        return iis_file_name + ".ilp"

    monkeypatch.setattr(pyomo_iis, "write_iis", fake_write_iis)

    analyzer = NativeIISAnalyzer(solver_name="gurobi_persistent", output_dir=str(tmp_path))
    report = analyzer.analyze(_model())

    assert calls["solver"] == "gurobi"
    assert "infeasibility_iis_gurobi" in calls["iis_file_name"]
    assert report.method == "native_iis:gurobi"
    assert report.iis_file == calls["iis_file_name"] + ".ilp"
    assert report.violations == []


def test_cplex_writes_iis_file_via_pyomo_wrapper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_write_iis(model, iis_file_name, solver=None):
        return iis_file_name + ".lp"

    monkeypatch.setattr(pyomo_iis, "write_iis", fake_write_iis)

    analyzer = NativeIISAnalyzer(solver_name="cplex", output_dir=str(tmp_path))
    report = analyzer.analyze(_model())

    assert report.method == "native_iis:cplex"
    assert report.iis_file.endswith(".lp")


def test_missing_solver_package_raises_clear_runtime_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_write_iis(model, iis_file_name, solver=None):
        raise ImportError("No module named 'gurobipy'")

    monkeypatch.setattr(pyomo_iis, "write_iis", fake_write_iis)

    analyzer = NativeIISAnalyzer(solver_name="gurobi", output_dir=str(tmp_path))

    with pytest.raises(RuntimeError, match="gurobi"):
        analyzer.analyze(_model())


def test_label_is_included_in_iis_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = {}

    def fake_write_iis(model, iis_file_name, solver=None):
        calls["iis_file_name"] = iis_file_name
        return iis_file_name

    monkeypatch.setattr(pyomo_iis, "write_iis", fake_write_iis)

    analyzer = NativeIISAnalyzer(
        solver_name="gurobi", output_dir=str(tmp_path), label="cenario_a"
    )
    analyzer.analyze(_model())

    assert calls["iis_file_name"].endswith("infeasibility_iis_gurobi_cenario_a")


def test_output_dir_is_created(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "reports"

    def fake_write_iis(model, iis_file_name, solver=None):
        return iis_file_name

    monkeypatch.setattr(pyomo_iis, "write_iis", fake_write_iis)

    analyzer = NativeIISAnalyzer(solver_name="gurobi", output_dir=str(output_dir))
    analyzer.analyze(_model())

    assert output_dir.exists()
