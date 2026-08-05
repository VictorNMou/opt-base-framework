import re

# Confirmado empiricamente pra ipopt (warmstart) e cyipopt/PyomoCyIpoptSolver
# (symbolic_solver_labels): interfaces com ConfigDict estrito rejeitam a chamada inteira quando
# recebem uma chave que não declaram — nunca ignoram silenciosamente. A mensagem é estável
# (pyomo/common/config.py, ConfigDict.set_value), então dá pra extrair qual chave foi rejeitada.
_UNSUPPORTED_KWARG_PATTERN = re.compile(r"key '(\w+)' not defined for ConfigDict")

# load_solutions=False é a única chave da qual a corretude do framework depende (permite
# _extract_values tratar infeasible sem o opt.solve() explodir sozinho) — nunca é descartada
# silenciosamente; se um solver a rejeitar, o erro original propaga em vez de continuar errado.
_REQUIRED_KWARGS = frozenset({"load_solutions"})

_unsupported_kwargs_by_solver: dict[str, set[str]] = {}


def solve_dropping_unsupported_kwargs(
    opt: object, model: object, solver_name: str, kwargs: dict[str, object]
) -> object:
    """Resolve descartando, por solver_name, kwargs que a interface do solver não aceita."""
    # Cada interface aceita um conjunto diferente de kwargs em .solve() — appsi_* é permissiva,
    # mas ipopt clássico e cyipopt usam ConfigDict estrito e rejeitam qualquer chave não
    # declarada. Não dá pra saber de antemão; a 1a chamada por solver_name aprende por
    # tentativa e erro (removendo uma chave rejeitada por vez) e cacheia pras próximas.
    known_unsupported = _unsupported_kwargs_by_solver.setdefault(solver_name, set())
    active_kwargs = {key: value for key, value in kwargs.items() if key not in known_unsupported}
    while True:
        try:
            return opt.solve(model, **active_kwargs)
        except ValueError as exc:
            rejected = _extract_rejected_kwarg(exc, active_kwargs)
            if rejected is None:
                raise
            known_unsupported.add(rejected)
            del active_kwargs[rejected]


def _extract_rejected_kwarg(exc: ValueError, active_kwargs: dict[str, object]) -> str | None:
    """Devolve o nome do kwarg rejeitado, ou None se o erro não for esse caso conhecido."""
    match = _UNSUPPORTED_KWARG_PATTERN.search(str(exc))
    if match is None:
        return None
    rejected = match.group(1)
    if rejected not in active_kwargs or rejected in _REQUIRED_KWARGS:
        return None
    return rejected
