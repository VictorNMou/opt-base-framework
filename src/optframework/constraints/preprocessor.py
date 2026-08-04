import pandas as pd


class ConstraintsPreprocessor:
    """Prepara estruturas de dados (sem Pyomo) para as regras de constraint."""

    def __init__(self, raw_data: dict[str, pd.DataFrame]) -> None:
        """Recebe as tabelas cruas de entrada."""
        self.raw_data = raw_data

    def preprocess(self) -> dict[str, object]:
        """Transforma as tabelas cruas em estruturas prontas para virar constraint."""
