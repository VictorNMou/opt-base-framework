import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Expressions(YamlComponentBuilder):
    """Anexa Expressions reutilizáveis por constraints/objective; model_expressions.yaml é opcional."""

    _CONFIG_FILENAME = "model_expressions.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao modelo as Expressions declaradas na configuração, se o arquivo existir."""
        config_path = self._config_path(data)
        if not config_path.exists():
            return
        config = self._load_config(config_path)
        rules_cls = self._import_rule(self._require(config, "rules_class"))
        rules = rules_cls(data)
        expressions = self._require(config, "expressions")
        for name, spec in expressions.items():
            spec = spec or {}
            self._attach_indexed_rule(
                model, name, spec, rules, pyo.Expression, overwrite=overwrite
            )
