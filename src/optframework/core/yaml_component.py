import importlib
from pathlib import Path
from typing import Any

import pyomo.environ as pyo
import yaml

from optframework.core.problem_data import ProblemData


class YamlComponentBuilder:
    """Mixin com infraestrutura comum aos artefatos YAML-driven do modelo."""

    _CONFIG_FILENAME: str

    def _config_path(self, data: ProblemData) -> Path:
        """Resolve o caminho do YAML do artefato dentro de `data.config_dir`."""
        return Path(data.config_dir) / self._CONFIG_FILENAME

    def _load_config(self, config_path: str | Path) -> dict[str, Any]:
        """Carrega o YAML de configuração do artefato."""
        with open(config_path, encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def _require(self, config: dict[str, Any], key: str) -> object:
        """Valida a presença de um campo obrigatório na configuração."""
        if key not in config:
            raise KeyError(
                f"Campo obrigatório '{key}' ausente em {self._CONFIG_FILENAME}."
            )
        return config[key]

    def _resolve_source(self, source: str, data: ProblemData) -> object:
        """Resolve `source: data.<atributo>` via getattr no ProblemData."""
        prefix = "data."
        if not source.startswith(prefix):
            raise ValueError(f"Fonte inválida '{source}': deve começar com '{prefix}'.")
        return getattr(data, source.removeprefix(prefix))

    def _import_rule(self, dotted_path: str) -> type:
        """Importa dinamicamente uma classe referenciada em config (`modulo.Classe`)."""
        module_path, _, class_name = dotted_path.rpartition(".")
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def _add_component(
        self,
        model: pyo.ConcreteModel,
        name: str,
        component: object,
        overwrite: bool = False,
    ) -> None:
        """Anexa (ou substitui) um componente Pyomo ao modelo pelo nome."""
        if hasattr(model, name):
            if not overwrite:
                raise ValueError(
                    f"Componente '{name}' já existe no modelo (overwrite=False)."
                )
            model.del_component(name)
        model.add_component(name, component)

    def _attach_indexed_rule(
        self,
        model: pyo.ConcreteModel,
        name: str,
        spec: dict[str, Any],
        rules: object,
        component_cls: type,
        overwrite: bool = False,
    ) -> None:
        """Resolve a rule e os index sets de `spec` e anexa o componente Pyomo (`Constraint`/`Expression`) ao modelo."""
        rule_fn = getattr(rules, name)
        index_sets = [
            getattr(model, index_name) for index_name in spec.get("index", [])
        ]
        self._add_component(
            model,
            name,
            component_cls(*index_sets, rule=rule_fn),
            overwrite=overwrite,
        )
