import pytest

from optframework.solver.solve_compat import solve_dropping_unsupported_kwargs


class _StrictSolver:
    """Simula uma interface com ConfigDict estrito: rejeita qualquer kwarg fora de `accepted`."""

    def __init__(self, accepted: set[str]) -> None:
        self.accepted = accepted
        self.calls: list[dict[str, object]] = []

    def solve(self, model: object, **kwargs: object) -> str:
        self.calls.append(dict(kwargs))
        for key in kwargs:
            if key not in self.accepted:
                raise ValueError(
                    f"key '{key}' not defined for ConfigDict '' and implicit "
                    "(undefined) keys are not allowed"
                )
        return "resultado"


def test_permissive_solver_receives_every_kwarg_on_first_try() -> None:
    solver = _StrictSolver(accepted={"tee", "symbolic_solver_labels", "load_solutions", "warmstart"})
    kwargs = {"tee": False, "symbolic_solver_labels": True, "load_solutions": False, "warmstart": False}

    result = solve_dropping_unsupported_kwargs(solver, object(), "permissivo", kwargs)

    assert result == "resultado"
    assert len(solver.calls) == 1
    assert solver.calls[0] == kwargs


def test_strict_solver_drops_single_rejected_kwarg() -> None:
    solver = _StrictSolver(accepted={"tee", "load_solutions"})
    kwargs = {"tee": False, "load_solutions": False, "warmstart": True}

    result = solve_dropping_unsupported_kwargs(solver, object(), "estrito-um-rejeitado", kwargs)

    assert result == "resultado"
    assert solver.calls[-1] == {"tee": False, "load_solutions": False}


def test_strict_solver_drops_multiple_rejected_kwargs_across_retries() -> None:
    solver = _StrictSolver(accepted={"tee", "load_solutions"})
    kwargs = {
        "tee": False,
        "symbolic_solver_labels": True,
        "load_solutions": False,
        "warmstart": True,
    }

    result = solve_dropping_unsupported_kwargs(solver, object(), "estrito-varios-rejeitados", kwargs)

    assert result == "resultado"
    assert solver.calls[-1] == {"tee": False, "load_solutions": False}
    assert len(solver.calls) == 3


def test_required_kwarg_is_never_dropped_and_error_propagates() -> None:
    solver = _StrictSolver(accepted={"tee"})
    kwargs = {"tee": False, "load_solutions": False}

    with pytest.raises(ValueError, match="load_solutions"):
        solve_dropping_unsupported_kwargs(solver, object(), "exige-load-solutions", kwargs)


def test_unrelated_value_error_is_not_swallowed() -> None:
    class _BrokenSolver:
        def solve(self, model: object, **kwargs: object) -> None:
            raise ValueError("modelo mal formado, sem relação com kwargs")

    with pytest.raises(ValueError, match="modelo mal formado"):
        solve_dropping_unsupported_kwargs(_BrokenSolver(), object(), "erro-generico", {"tee": False})


def test_rejection_is_cached_across_calls_for_same_solver_name() -> None:
    solver = _StrictSolver(accepted={"tee", "load_solutions"})
    kwargs = {"tee": False, "load_solutions": False, "warmstart": True}

    solve_dropping_unsupported_kwargs(solver, object(), "cache-mesmo-solver", kwargs)
    assert len(solver.calls) == 2

    solve_dropping_unsupported_kwargs(solver, object(), "cache-mesmo-solver", kwargs)
    assert len(solver.calls) == 3
    assert solver.calls[-1] == {"tee": False, "load_solutions": False}
