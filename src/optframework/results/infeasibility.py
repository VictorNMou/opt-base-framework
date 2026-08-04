from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstraintViolation:
    """Uma constraint (ou lado de uma constraint ranged) candidata a causa da infeasibilidade."""

    constraint_name: str
    index: Any = None
    side: str | None = None
    slack: float | None = None


@dataclass
class InfeasibilityReport:
    """Diagnóstico de infeasibilidade — via relaxamento elástico ou IIS nativo do solver."""

    method: str
    violations: list[ConstraintViolation] = field(default_factory=list)
    suspected_bound_conflict: bool = False
    relaxed_termination_condition: Any = None
    iis_file: str | None = None

    def render(self) -> str:
        """Formata o diagnóstico em texto legível, cobrindo os quatro estados possíveis."""
        if self.method.startswith("native_iis"):
            return (
                f"Diagnóstico nativo ({self.method}): IIS gravado em '{self.iis_file}'. "
                "Abra o arquivo (formato LP) para ver as constraints/bounds em conflito."
            )
        if self.suspected_bound_conflict:
            return (
                "Relaxamento elástico não encontrou solução mesmo com slack ilimitado em toda "
                "constraint — suspeite de conflito em bounds/domínio de variável ou valores fixados "
                "(fix()), não em uma constraint geral."
            )
        if not self.violations:
            return (
                "Relaxamento elástico resolveu, mas nenhuma constraint passou da tolerância de "
                "slack — diagnóstico inconclusivo (possível infeasibilidade numericamente marginal)."
            )
        linhas = [
            f"- {v.constraint_name}"
            + (f"[{v.index}]" if v.index is not None else "")
            + (f" ({v.side})" if v.side else "")
            + f": slack={v.slack:.6g}"
            for v in sorted(self.violations, key=lambda v: v.slack or 0.0, reverse=True)
        ]
        return "Constraints candidatas a causa da infeasibilidade (ordenadas por slack):\n" + "\n".join(
            linhas
        )
