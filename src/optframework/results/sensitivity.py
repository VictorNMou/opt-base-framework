from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstraintDual:
    """Dual (shadow price) de uma constraint, obtido via fix-and-resolve."""

    constraint_name: str
    index: Any = None
    dual: float = 0.0


@dataclass
class VariableReducedCost:
    """Custo reduzido de uma variável que permaneceu contínua e livre no fix-and-resolve."""

    var_name: str
    index: Any = None
    reduced_cost: float | None = None


@dataclass
class SensitivityReport:
    """Diagnóstico de sensibilidade: duais e custos reduzidos via fix-and-resolve de não-contínuas."""

    method: str = "fix_and_resolve"
    duals: list[ConstraintDual] = field(default_factory=list)
    reduced_costs: list[VariableReducedCost] = field(default_factory=list)
    fixed_variable_count: int = 0
    resolved: bool = True

    def render(self) -> str:
        """Formata o diagnóstico em texto legível, incluindo o alerta do caso degenerado."""
        if not self.resolved:
            return (
                "Sensibilidade: o resolve com variáveis não-contínuas fixadas não convergiu — "
                "nenhum dual disponível."
            )
        aviso = (
            f"\n\nAviso: {self.fixed_variable_count} variável(is) não-contínua(s) foram "
            "fixadas para permitir os duais. Se todas as variáveis do problema são "
            "binárias/inteiras, os duais tendem a ficar zerados (não há margem contínua para "
            "precificar) — isso é esperado, não um erro."
            if self.fixed_variable_count > 0
            else ""
        )
        if not self.duals:
            return "Sensibilidade: nenhuma constraint ativa para reportar dual." + aviso
        linhas = [
            f"- {d.constraint_name}"
            + (f"[{d.index}]" if d.index is not None else "")
            + f": dual={d.dual:.6g}"
            for d in self.duals
        ]
        texto = "Duais por constraint:\n" + "\n".join(linhas)
        if self.reduced_costs:
            rc_linhas = [
                f"- {r.var_name}"
                + (f"[{r.index}]" if r.index is not None else "")
                + f": rc={'N/A' if r.reduced_cost is None else f'{r.reduced_cost:.6g}'}"
                for r in self.reduced_costs
            ]
            texto += "\n\nCustos reduzidos (variáveis contínuas livres):\n" + "\n".join(
                rc_linhas
            )
        return texto + aviso
