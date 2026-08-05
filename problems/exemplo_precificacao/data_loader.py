from dataclasses import dataclass
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent / "config"


@dataclass
class PrecificacaoData:
    """Dados do problema de precificação com elasticidade própria e cruzada (contrato ProblemData)."""

    config_dir: str
    produtos: list[str]
    preco_base: dict[str, float]
    quantidade_base: dict[str, float]
    custo: dict[str, float]
    elasticidade_propria: dict[str, float]
    elasticidade_cruzada: dict[tuple[str, str], float]
    capacidade_total: float


def load_data() -> PrecificacaoData:
    """Monta uma instância fictícia de 3 produtos substitutos (linha básico/intermediário/premium)."""
    produtos = ["Basico", "Intermediario", "Premium"]
    return PrecificacaoData(
        config_dir=str(_CONFIG_DIR),
        produtos=produtos,
        preco_base={"Basico": 50.0, "Intermediario": 100.0, "Premium": 200.0},
        quantidade_base={"Basico": 1000.0, "Intermediario": 500.0, "Premium": 150.0},
        custo={"Basico": 30.0, "Intermediario": 55.0, "Premium": 120.0},
        elasticidade_propria={"Basico": -2.5, "Intermediario": -2.2, "Premium": -1.8},
        elasticidade_cruzada={
            ("Basico", "Intermediario"): 0.3,
            ("Basico", "Premium"): 0.1,
            ("Intermediario", "Basico"): 0.3,
            ("Intermediario", "Premium"): 0.2,
            ("Premium", "Basico"): 0.1,
            ("Premium", "Intermediario"): 0.2,
        },
        capacidade_total=1000.0,
    )
