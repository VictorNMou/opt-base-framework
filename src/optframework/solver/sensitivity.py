import pyomo.environ as pyo

from optframework.results.sensitivity import (
    ConstraintDual,
    SensitivityReport,
    VariableReducedCost,
)
from optframework.solver.solve_compat import solve_with_compat


class SensitivityAnalyzer:
    """Extrai duais/custos reduzidos fixando variáveis não-contínuas e resolvendo com Suffix dual."""

    def __init__(
        self,
        solver_name: str,
        options: dict[str, object] | None = None,
        label: str | None = None,
    ) -> None:
        """Guarda o solver_name do profile ativo (nunca suas options) e o label do cenário."""
        self.solver_name = solver_name
        self.options = options or {}
        self.label = label

    def analyze(self, model: pyo.ConcreteModel) -> SensitivityReport:
        """Clona o modelo já resolvido, fixa variáveis não-contínuas em Reals e resolve com dual/rc."""
        sens = model.clone()
        fixed_vars = self._fix_non_continuous_vars(sens)

        sens.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
        sens.rc = pyo.Suffix(direction=pyo.Suffix.IMPORT)

        opt = pyo.SolverFactory(self.solver_name)
        raw_results = solve_with_compat(opt, sens, self.solver_name, self.options)

        if len(raw_results.solution) == 0:
            return SensitivityReport(
                resolved=False, fixed_variable_count=len(fixed_vars)
            )

        sens.solutions.load_from(raw_results)
        return SensitivityReport(
            duals=self._extract_duals(sens),
            reduced_costs=self._extract_reduced_costs(sens, fixed_vars),
            fixed_variable_count=len(fixed_vars),
        )

    def _fix_non_continuous_vars(self, model: pyo.ConcreteModel) -> list[object]:
        """Troca o domínio de variáveis binárias/inteiras para Reals e fixa no valor resolvido."""
        fixed = []
        for var in model.component_data_objects(pyo.Var, active=True):
            if not var.is_continuous():
                value = var.value
                var.domain = pyo.Reals
                var.fix(value)
                fixed.append(var)
        return fixed

    def _extract_duals(self, model: pyo.ConcreteModel) -> list[ConstraintDual]:
        """Lê o dual de cada constraint ativa (0.0 quando o solver não populou)."""
        return [
            ConstraintDual(
                c.parent_component().local_name, c.index(), model.dual.get(c, 0.0)
            )
            for c in model.component_data_objects(pyo.Constraint, active=True)
        ]

    def _extract_reduced_costs(
        self, model: pyo.ConcreteModel, fixed_vars: list[object]
    ) -> list[VariableReducedCost]:
        """Lê o custo reduzido das variáveis que permaneceram livres (None se o solver não popula)."""
        fixed_ids = {id(var) for var in fixed_vars}
        return [
            VariableReducedCost(
                var.parent_component().local_name, var.index(), model.rc.get(var)
            )
            for var in model.component_data_objects(pyo.Var, active=True)
            if id(var) not in fixed_ids
        ]
