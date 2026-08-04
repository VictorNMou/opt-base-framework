import pyomo.environ as pyo

from optframework.results.result import Result
from optframework.solver.adapter import SolverAdapter


class PyomoAdapter(SolverAdapter):
    """Implementação de SolverAdapter via Pyomo, com solver selecionado por perfil."""

    def solve(self, model: pyo.ConcreteModel, profile: str = "default") -> Result:
        """Resolve o modelo via Pyomo, usando o perfil configurado em model_solver.yaml."""

    def get_results(self) -> Result:
        """Devolve o resultado bruto do último solve."""
