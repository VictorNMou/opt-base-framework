import os

# Precisa ser setado antes de qualquer import que carregue o libomp/libdmumps bundlados no
# pipipopt — o wheel traz sua própria cópia de OpenMP, que aborta o processo (SIGABRT dentro de
# libdmumps_seq/dmumpsid_) se detectar outra já carregada (numpy/scipy trazem a delas). setdefault
# preserva o valor do usuário caso ele já tenha configurado algo diferente.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path

import pyomo.environ as pyo
import pytest

from optframework.solver.pyomo_adapter import PyomoAdapter

pytestmark = pytest.mark.skipif(
    not pyo.SolverFactory("cyipopt").available(exception_flag=False),
    reason="cyipopt (extra opcional 'cyipopt', pacote pipipopt) não instalado neste ambiente",
)


def _write_config(tmp_path: Path) -> None:
    (tmp_path / "model_solver.yaml").write_text(
        "profiles:\n  default:\n    solver_name: cyipopt\n    tee: false\n    options: {}\n"
    )


def test_solve_returns_optimal_result(tmp_path: Path) -> None:
    # pylint: disable=duplicate-code
    _write_config(tmp_path)
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals, initialize=1.0)
    model.obj = pyo.Objective(expr=(model.x - 2) ** 2)

    result = PyomoAdapter(config_dir=tmp_path).solve(model)

    assert result.termination_condition == pyo.TerminationCondition.optimal
    assert result.values[("x", None)] == pytest.approx(2.0, abs=1e-4)


def test_options_are_applied_via_solve_kwarg_not_options_attribute(tmp_path: Path) -> None:
    (tmp_path / "model_solver.yaml").write_text(
        "profiles:\n"
        "  default:\n"
        "    solver_name: cyipopt\n"
        "    tee: false\n"
        "    options:\n"
        "      max_iter: 1\n"
    )
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals, initialize=1.0)
    model.obj = pyo.Objective(expr=(model.x - 2) ** 2)

    result = PyomoAdapter(config_dir=tmp_path).solve(model)

    assert result.termination_condition != pyo.TerminationCondition.optimal
