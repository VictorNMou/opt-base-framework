import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Objective(YamlComponentBuilder):
    """Anexa a função-objetivo ativa (selecionada por perfil) ao modelo."""

    _CONFIG_FILENAME = "model_objective.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, profile: str = "default"
    ) -> None:
        """Anexa o Objective (nome fixo 'obj') correspondente ao perfil escolhido."""
