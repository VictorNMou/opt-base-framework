import pyomo.environ as pyo

from optframework.core.problem_data import ProblemData
from optframework.core.yaml_component import YamlComponentBuilder

_DOMAIN_MAP = {
    "Reals": pyo.Reals,
    "NonNegativeReals": pyo.NonNegativeReals,
    "Integers": pyo.Integers,
    "NonNegativeIntegers": pyo.NonNegativeIntegers,
    "Binary": pyo.Binary,
}


class Variables(YamlComponentBuilder):
    """Declara as Variables de decisão do modelo a partir de configuração YAML."""

    _CONFIG_FILENAME = "model_variables.yaml"

    def attach_to_model(
        self, model: pyo.ConcreteModel, data: ProblemData, overwrite: bool = False
    ) -> None:
        """Anexa ao ConcreteModel as Variables declaradas no YAML."""
        config = self._load_config(self._config_path(data))
        variables = self._require(config, "variables")
        for name, spec in variables.items():
            index_sets = [
                getattr(model, index_name) for index_name in spec.get("index", [])
            ]
            kwargs: dict[str, object] = {}
            if "within" in spec:
                kwargs["within"] = getattr(model, spec["within"])
            else:
                kwargs["domain"] = _DOMAIN_MAP[spec.get("domain", "Reals")]
            if "bounds" in spec:
                kwargs["bounds"] = self._resolve_bounds(spec["bounds"], data)
            var = pyo.Var(*index_sets, **kwargs)
            self._add_component(model, name, var, overwrite=overwrite)

    def _resolve_bounds(self, bounds: list, data: ProblemData) -> object:
        """
        Resolve `bounds: [lower, upper]` pro formato aceito por `pyo.Var(bounds=...)`.

        Cada lado é literal (número/`null`) ou `data.<atributo>`, resolvido por índice via
        `_resolve_source` (mesmo mecanismo de Parameters). Se algum lado vier de um `dict`
        (bound por índice), devolve uma rule; senão devolve a tupla `(lower, upper)` direto.
        """
        lower, upper = (self._resolve_bound_side(side, data) for side in bounds)
        if isinstance(lower, dict) or isinstance(upper, dict):

            def bounds_rule(
                model: pyo.ConcreteModel, *idx: object
            ) -> tuple[object, object]:
                key = idx[0] if len(idx) == 1 else idx
                lo = lower[key] if isinstance(lower, dict) else lower
                hi = upper[key] if isinstance(upper, dict) else upper
                return (lo, hi)

            return bounds_rule
        return (lower, upper)

    def _resolve_bound_side(self, side: object, data: ProblemData) -> object:
        """Resolve um lado do bound: literal (número/`None`) passa direto, `data.<atributo>` é lido do data."""
        if isinstance(side, str) and side.startswith("data."):
            return self._resolve_source(side, data)
        return side
