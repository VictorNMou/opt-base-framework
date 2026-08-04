from typing import Protocol

import pyomo.environ as pyo

from optframework.results.result import Result


class SolverAdapter(Protocol):
    """Contrato de abstração sobre o solver físico."""

    def solve(self, model: pyo.ConcreteModel, profile: str = "default") -> Result:
        """Resolve o modelo segundo o perfil informado."""
        ...

    def get_results(self) -> Result:
        """Devolve o resultado bruto do último solve."""
        ...
