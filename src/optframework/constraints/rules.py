from typing import Any

import pyomo.environ as pyo


class ConstraintRules:
    """Implementa a matemática Pyomo das constraints a partir de dados pré-processados."""

    def __init__(self, preprocessed: dict[str, Any]) -> None:
        """Recebe as estruturas já prontas do ConstraintsPreprocessor."""
        self.preprocessed = preprocessed

    def build_rule(self, model: pyo.ConcreteModel, name: str) -> object | None:
        """Devolve a expressão/regra Pyomo da constraint nomeada, ou None se degenerada."""
        raise NotImplementedError
