import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Constraints(YamlComponentBuilder):
    """Decide, por família declarada em config, se está ligada e anexa a constraint ao modelo."""

    _CONFIG_FILENAME = "model_constraints.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao modelo as famílias de constraint ativas na configuração."""
