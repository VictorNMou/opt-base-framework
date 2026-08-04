import math

from optframework.results.metrics import SolveMetrics

_EPSILON = 1e-10


def build_solve_metrics(raw_results: object, wall_time_seconds: float) -> SolveMetrics:
    """Monta SolveMetrics a partir de raw_results.problem (schema padrão do Pyomo) e do tempo medido."""
    lower_bound = _safe_bound(raw_results.problem.lower_bound)
    upper_bound = _safe_bound(raw_results.problem.upper_bound)
    gap = None
    if lower_bound is not None and upper_bound is not None:
        denom = max(abs(upper_bound), abs(lower_bound), _EPSILON)
        gap = abs(upper_bound - lower_bound) / denom
    return SolveMetrics(
        wall_time_seconds=wall_time_seconds,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        gap=gap,
    )


def _safe_bound(value: float | None) -> float | None:
    """Trata None e infinito (bound não populado pelo solver) como indisponível."""
    if value is None or math.isinf(value):
        return None
    return float(value)
