from typing import Any

import pyomo.environ as pyo


class YamlComponentBuilder:
    """Mixin com infraestrutura comum aos artefatos YAML-driven do modelo."""

    _CONFIG_FILENAME: str

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Carrega o YAML de configuração do artefato."""

    def _require(self, config: dict[str, Any], key: str) -> object:
        """Valida a presença de um campo obrigatório na configuração."""

    def _add_component(
        self,
        model: pyo.ConcreteModel,
        name: str,
        component: object,
        overwrite: bool = False,
    ) -> None:
        """Anexa (ou substitui) um componente Pyomo ao modelo pelo nome."""
