import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Sets(YamlComponentBuilder):
    """Declara os Sets do modelo a partir de configuração YAML."""

    _CONFIG_FILENAME = "model_sets.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao ConcreteModel os Sets declarados no YAML."""
        config = self._load_config(self._config_path(data))
        sets = self._require(config, "sets")
        for name, spec in sets.items():
            members = self._resolve_source(self._require(spec, "source"), data)
            self._add_component(
                model, name, pyo.Set(initialize=list(members)), overwrite=overwrite
            )
