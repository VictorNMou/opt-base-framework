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
        config = self._load_config(self._config_path(data))
        rules_cls = self._import_rule(self._require(config, "rules_class"))
        rules = rules_cls(data)
        families = self._require(config, "constraints")
        for name, spec in families.items():
            if not spec.get("enabled", True):
                continue
            rule_fn = getattr(rules, name)
            self._add_component(
                model, name, pyo.Constraint(rule=rule_fn), overwrite=overwrite
            )
