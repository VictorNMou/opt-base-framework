import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Parameters(YamlComponentBuilder):
    """Declara os Parameters do modelo a partir de configuração YAML."""

    _CONFIG_FILENAME = "model_parameters.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao ConcreteModel os Parameters declarados no YAML."""
        config = self._load_config(self._config_path(data))
        parameters = self._require(config, "parameters")
        for name, spec in parameters.items():
            values = self._resolve_source(self._require(spec, "source"), data)
            index_sets = [getattr(model, index_name) for index_name in spec.get("index", [])]
            mutable = spec.get("mutable", False)
            kwargs = {"initialize": values, "mutable": mutable}
            if "default" in spec:
                kwargs["default"] = spec["default"]
            if "within" in spec:
                kwargs["within"] = getattr(model, spec["within"])
            param = pyo.Param(*index_sets, **kwargs)
            self._add_component(model, name, param, overwrite=overwrite)
