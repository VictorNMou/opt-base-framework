from types import SimpleNamespace


class CyIpoptLikeSolver:
    """Simula PyomoCyIpoptSolver: sem `.options`, rejeita `symbolic_solver_labels` no .solve()."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def solve(self, model: object, **kwargs: object) -> SimpleNamespace:
        self.calls.append(dict(kwargs))
        if "symbolic_solver_labels" in kwargs:
            raise ValueError(
                "key 'symbolic_solver_labels' not defined for ConfigDict '' and implicit "
                "(undefined) keys are not allowed"
            )
        return SimpleNamespace(
            solution=[], solver=SimpleNamespace(termination_condition="infeasible")
        )
