from dataclasses import dataclass


@dataclass
class SolveMetrics:
    """
    Métricas do solve: tempo de parede (medido em Python) e bounds/gap do schema do Pyomo.

    `gap` é magnitude pura (|upper - lower| / max(|upper|, |lower|, epsilon)), não um gap
    assinado/relativo a um sentido (minimize/maximize) específico.
    """

    wall_time_seconds: float
    lower_bound: float | None = None
    upper_bound: float | None = None
    gap: float | None = None
