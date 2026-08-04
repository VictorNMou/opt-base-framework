from collections.abc import Callable
from pathlib import Path

import pyomo.environ as pyo


class Reporter:
    """Grava snapshots de texto do modelo (pprint antes / display depois) em disco."""

    def __init__(self, output_dir: str) -> None:
        """Cria (se necessário) o diretório de saída dos relatórios."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_before(self, model: pyo.ConcreteModel, label: str | None = None) -> Path:
        """Grava a estrutura do modelo (pprint) antes do solve."""
        return self._write(model.pprint, "pprint_before", label)

    def write_after(self, model: pyo.ConcreteModel, label: str | None = None) -> Path:
        """Grava os valores resolvidos do modelo (display) depois do solve."""
        return self._write(model.display, "display_after", label)

    def _write(
        self, dump: Callable[..., None], kind: str, label: str | None
    ) -> Path:
        suffix = f"_{label}" if label else ""
        path = self.output_dir / f"{kind}{suffix}.txt"
        with open(path, "w", encoding="utf-8") as file:
            dump(ostream=file)
        return path
