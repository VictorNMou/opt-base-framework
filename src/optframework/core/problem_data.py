from typing import Protocol


class ProblemData(Protocol):
    """Contrato de dados que cada problema concreto fornece ao Model."""

    config_dir: str
