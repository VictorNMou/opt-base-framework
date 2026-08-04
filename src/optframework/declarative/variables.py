import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder

_DOMAIN_MAP = {
    "Reals": pyo.Reals,
    "NonNegativeReals": pyo.NonNegativeReals,
    "Integers": pyo.Integers,
    "NonNegativeIntegers": pyo.NonNegativeIntegers,
    "Binary": pyo.Binary,
}


class Variables(YamlComponentBuilder):
    """Declara as Variables de decisão do modelo a partir de configuração YAML."""

    _CONFIG_FILENAME = "model_variables.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao ConcreteModel as Variables declaradas no YAML."""
        config = self._load_config(self._config_path(data))
        variables = self._require(config, "variables")
        for name, spec in variables.items():
            index_sets = [getattr(model, index_name) for index_name in spec.get("index", [])]
            domain = _DOMAIN_MAP[spec.get("domain", "Reals")]
            var = pyo.Var(*index_sets, domain=domain)
            self._add_component(model, name, var, overwrite=overwrite)
