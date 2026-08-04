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
