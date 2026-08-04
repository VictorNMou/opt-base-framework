from dataclasses import dataclass
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent / "config"


@dataclass
class KnapsackData:
    """Dados do problema de knapsack 0/1 (contrato ProblemData)."""

    config_dir: str
    items: list[str]
    peso: dict[str, float]
    valor: dict[str, float]
    capacidade: float


def load_data() -> KnapsackData:
    """Monta a instância clássica de knapsack (pesos/valores/capacidade fictícios)."""
    return KnapsackData(
        config_dir=str(_CONFIG_DIR),
        items=["A", "B", "C"],
        peso={"A": 10, "B": 20, "C": 30},
        valor={"A": 60, "B": 100, "C": 120},
        capacidade=50,
    )
