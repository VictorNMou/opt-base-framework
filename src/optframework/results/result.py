from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    """Resultado bruto de um solve, sem interpretação de status."""

    termination_condition: Any
    values: dict[str, Any]
