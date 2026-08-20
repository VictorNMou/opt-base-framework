import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder


class Constraints(YamlComponentBuilder):
    """Anexa ao modelo todas as famílias de constraint declaradas em config e, à parte, liga/desliga cada uma."""

    _CONFIG_FILENAME = "model_constraints.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao modelo todas as famílias de constraint declaradas na configuração, sem decidir se ficam ativas."""
        config = self._load_config(self._config_path(data))
        rules_cls = self._import_rule(self._require(config, "rules_class"))
        rules = rules_cls(data)
        families = self._require(config, "constraints")
        for name, spec in families.items():
            spec = spec or {}
            self._attach_indexed_rule(
                model, name, spec, rules, pyo.Constraint, overwrite=overwrite
            )

    def apply_enabled(self, model: pyo.ConcreteModel, data: ProblemData) -> None:
        """Liga/desliga cada constraint já anexada conforme o `enabled` (bool) estático de cada família na configuração."""
        config = self._load_config(self._config_path(data))
        families = self._require(config, "constraints")
        enabled = {
            name: (spec or {}).get("enabled", True) for name, spec in families.items()
        }
        self.set_enabled(model, enabled)

    def set_enabled(self, model: pyo.ConcreteModel, enabled: dict[str, bool]) -> None:
        """Liga/desliga ad-hoc, por nome, constraints já anexadas ao modelo — sem passar pela configuração."""
        for name, is_enabled in enabled.items():
            if not hasattr(model, name):
                raise KeyError(
                    f"Constraint '{name}' não está anexada ao modelo — confira o nome "
                    "ou se 'attach_to_model' já rodou antes de 'set_enabled'."
                )
            component = getattr(model, name)
            if is_enabled:
                component.activate()
            else:
                component.deactivate()
