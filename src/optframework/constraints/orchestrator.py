import pyomo.environ as pyo

from optframework.constraints.base import ConstraintRule
from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Constraints(YamlComponentBuilder):
    """Decide, por família declarada em config, se está ligada e anexa a constraint ao modelo."""

    _CONFIG_FILENAME = "model_constraints.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao modelo as famílias de constraint ativas na configuração."""
        config = self._load_config(self._config_path(data))
        families = self._require(config, "constraints")
        for spec in families.values():
            if not spec.get("enabled", True):
                continue
            rule_cls = self._import_rule(self._require(spec, "rule"))
            rule: ConstraintRule = rule_cls()
            rule.build(model, data)
