from dataclasses import dataclass
from typing import Any

import pyomo.environ as pyo

from optframework.results.infeasibility import InfeasibilityReport
from optframework.results.metrics import SolveMetrics
from optframework.results.sensitivity import SensitivityReport

INFEASIBLE_TERMINATION_CONDITIONS = frozenset(
    {
        pyo.TerminationCondition.infeasible,
        pyo.TerminationCondition.infeasibleOrUnbounded,
    }
)


@dataclass
class Result:
    """Resultado bruto de um solve, sem interpretação de status."""

    termination_condition: Any
    values: dict[tuple[str, Any], Any]
    infeasibility: InfeasibilityReport | None = None
    metrics: SolveMetrics | None = None
    sensitivity: SensitivityReport | None = None

    @property
    def is_infeasible(self) -> bool:
        """True se termination_condition indica infeasibilidade."""
        return self.termination_condition in INFEASIBLE_TERMINATION_CONDITIONS
