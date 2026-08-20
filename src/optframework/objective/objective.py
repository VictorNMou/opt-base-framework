import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder

_SENSE_MAP = {
    "minimize": pyo.minimize,
    "maximize": pyo.maximize,
}


class Objective(YamlComponentBuilder):
    """Anexa ao modelo todos os objectives declarados em config e, à parte, decide qual fica ativo."""

    _CONFIG_FILENAME = "model_objective.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao modelo todos os objectives declarados na configuração, sem decidir qual fica ativo."""
        config = self._load_config(self._config_path(data))
        rules_cls = self._import_rule(self._require(config, "rules_class"))
        rules = rules_cls(data)
        objectives = self._require(config, "objectives")
        for name, spec in objectives.items():
            spec = spec or {}
            rule_fn = getattr(rules, name)
            sense = _SENSE_MAP[spec.get("sense", "minimize")]
            self._add_component(
                model, name, pyo.Objective(rule=rule_fn, sense=sense), overwrite=overwrite
            )

    def apply_profile(
        self, model: pyo.ConcreteModel, data: ProblemData, profile: str | None = None
    ) -> None:
        """Ativa o objective do perfil escolhido (ou o `default` da config) e desativa os demais já anexados."""
        config = self._load_config(self._config_path(data))
        objectives = self._require(config, "objectives")
        if profile is None:
            profile = self._require(config, "default")
        if profile not in objectives:
            raise KeyError(
                f"Perfil de objetivo '{profile}' não encontrado em {self._CONFIG_FILENAME}."
            )
        self.set_active(model, profile)

    def set_active(self, model: pyo.ConcreteModel, name: str) -> None:
        """Ativa ad-hoc um único objective por nome, desativando todos os demais já anexados ao modelo."""
        objectives = list(model.component_objects(pyo.Objective))
        if not any(objective.name == name for objective in objectives):
            raise KeyError(
                f"Objective '{name}' não está anexado ao modelo — "
                f"anexados: {sorted(objective.name for objective in objectives)}."
            )
        for objective in objectives:
            if objective.name == name:
                objective.activate()
            else:
                objective.deactivate()
