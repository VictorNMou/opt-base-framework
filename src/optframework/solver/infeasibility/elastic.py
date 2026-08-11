import pyomo.environ as pyo

from optframework.results.infeasibility import ConstraintViolation, InfeasibilityReport
from optframework.solver.solve_compat import solve_with_compat

_SLACK_COMPONENT_NAMES = (
    "infeasibility_slacks",
    "infeasibility_constraints",
    "infeasibility_objective",
)


class ElasticRelaxationAnalyzer:
    """Diagnostica infeasibilidade injetando slack em toda constraint e minimizando o total (Chinneck)."""

    def __init__(
        self,
        solver_name: str,
        options: dict[str, object] | None = None,
        tolerance: float = 1e-6,
        output_dir: str | None = None,
        label: str | None = None,
    ) -> None:
        """Guarda só o solver_name do profile ativo (nunca suas options) e a tolerância de violação."""
        self.solver_name = solver_name
        self.options = options or {}
        self.tolerance = tolerance

    def analyze(self, model: pyo.ConcreteModel) -> InfeasibilityReport:
        """Clona o modelo, relaxa todas as constraints ativas com slack e resolve minimizando o total."""
        relaxed = model.clone()
        for name in _SLACK_COMPONENT_NAMES:
            if hasattr(relaxed, name):
                raise ValueError(
                    f"Componente '{name}' já existe no modelo; renomeie-o antes do diagnóstico."
                )

        self._deactivate_objectives(relaxed)
        meta = self._elasticize(relaxed)

        opt = pyo.SolverFactory(self.solver_name)
        raw_results = solve_with_compat(opt, relaxed, self.solver_name, self.options)

        if len(raw_results.solution) == 0:
            return InfeasibilityReport(
                method="elastic_relaxation",
                violations=[],
                suspected_bound_conflict=True,
                relaxed_termination_condition=raw_results.solver.termination_condition,
            )

        relaxed.solutions.load_from(raw_results)
        violations = self._extract_violations(meta)
        return InfeasibilityReport(
            method="elastic_relaxation",
            violations=violations,
            suspected_bound_conflict=False,
            relaxed_termination_condition=raw_results.solver.termination_condition,
        )

    def _deactivate_objectives(self, model: pyo.ConcreteModel) -> None:
        """Desativa todos os objectives originais antes de otimizar o slack total."""
        for objective in model.component_objects(pyo.Objective, active=True):
            objective.deactivate()

    def _elasticize(self, model: pyo.ConcreteModel) -> list[tuple]:
        """Substitui cada constraint ativa por versão(ões) com slack; devolve metadados p/ o relatório."""
        targets = list(model.component_data_objects(pyo.Constraint, active=True))
        captured = [
            (
                c.parent_component().local_name,
                c.index(),
                c.equality,
                None if c.lower is None else pyo.value(c.lower),
                None if c.upper is None else pyo.value(c.upper),
                c.body,
            )
            for c in targets
        ]
        for c in targets:
            c.deactivate()

        model.infeasibility_slacks = pyo.VarList(domain=pyo.NonNegativeReals)
        model.infeasibility_constraints = pyo.ConstraintList()
        meta: list[tuple] = []

        for name, index, equality, lower, upper, body in captured:
            if equality:
                slack_pos = model.infeasibility_slacks.add()
                slack_neg = model.infeasibility_slacks.add()
                model.infeasibility_constraints.add(
                    body + slack_neg - slack_pos == lower
                )
                meta.append((name, index, "eq", slack_pos, slack_neg))
                continue
            if lower is not None:
                slack = model.infeasibility_slacks.add()
                model.infeasibility_constraints.add(body + slack >= lower)
                meta.append((name, index, "lower", slack, None))
            if upper is not None:
                slack = model.infeasibility_slacks.add()
                model.infeasibility_constraints.add(body - slack <= upper)
                meta.append((name, index, "upper", slack, None))

        model.infeasibility_objective = pyo.Objective(
            expr=sum(model.infeasibility_slacks[i] for i in model.infeasibility_slacks),
            sense=pyo.minimize,
        )
        return meta

    def _extract_violations(self, meta: list[tuple]) -> list[ConstraintViolation]:
        """Filtra slacks acima da tolerância e ordena por magnitude decrescente."""
        violations = []
        for name, index, side, slack_pos, slack_neg in meta:
            slack = pyo.value(slack_pos) + (
                pyo.value(slack_neg) if slack_neg is not None else 0.0
            )
            if slack > self.tolerance:
                violations.append(ConstraintViolation(name, index, side, slack))
        violations.sort(key=lambda v: v.slack, reverse=True)
        return violations
