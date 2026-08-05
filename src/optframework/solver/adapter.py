from typing import Protocol

import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.results.result import Result


class SolverAdapter(Protocol):
    """Contrato de abstração sobre o solver físico."""

    def solve(
        self,
        model: pyo.ConcreteModel,
        profile: str = "default",
        label: str | None = None,
        data: ProblemData | None = None,
        warmstart: bool = False,
    ) -> Result:
        """Resolve o modelo; `label` identifica a rodada para nomear relatórios."""
        ...

    def get_results(self) -> Result:
        """Devolve o resultado bruto do último solve."""
        ...
