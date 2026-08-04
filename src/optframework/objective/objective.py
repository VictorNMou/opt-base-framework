import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder

_SENSE_MAP = {
    "minimize": pyo.minimize,
    "maximize": pyo.maximize,
}


class Objective(YamlComponentBuilder):
    """Anexa os objectives declarados em config, ativando só o do perfil escolhido."""

    _CONFIG_FILENAME = "model_objective.yaml"

    def attach_to_model(
        self,
        model: pyo.ConcreteModel,
        data: ProblemData,
        profile: str | None = None,
        overwrite: bool = False,
    ) -> None:
        """Anexa todos os objectives declarados e ativa só o do perfil escolhido."""
        config = self._load_config(self._config_path(data))
        rules_cls = self._import_rule(self._require(config, "rules_class"))
        rules = rules_cls(data)
        objectives = self._require(config, "objectives")
        if profile is None:
            profile = self._require(config, "default")
        if profile not in objectives:
            raise KeyError(f"Perfil de objetivo '{profile}' não encontrado em {self._CONFIG_FILENAME}.")

        for name, spec in objectives.items():
            if overwrite or not hasattr(model, name):
                rule_fn = getattr(rules, name)
                sense = _SENSE_MAP[spec.get("sense", "minimize")]
                self._add_component(
                    model, name, pyo.Objective(rule=rule_fn, sense=sense), overwrite=overwrite
                )
            component = getattr(model, name)
            if name == profile:
                component.activate()
            else:
                component.deactivate()
