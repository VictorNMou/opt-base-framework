import pyomo.environ as pyo

from optframework.constraints.orchestrator import Constraints
from optframework.core.problem_data import ProblemData
from optframework.core.validation import validate_problem_config
from optframework.declarative.expressions import Expressions
from optframework.declarative.parameters import Parameters
from optframework.declarative.sets import Sets
from optframework.declarative.variables import Variables
from optframework.logging import logger
from optframework.objective.objective import Objective


class Model:
    """Orquestra a montagem do modelo Pyomo a partir dos artefatos do framework."""

    def __init__(self, data: ProblemData) -> None:
        """Armazena os dados do problema e inicializa os artefatos do modelo."""
        self.data: ProblemData = data
        self.model: pyo.ConcreteModel = pyo.ConcreteModel()
        self.sets: Sets = Sets()
        self.parameters: Parameters = Parameters()
        self.variables: Variables = Variables()
        self.expressions: Expressions = Expressions()
        self.constraints: Constraints = Constraints()
        self.objective: Objective = Objective()

    def build(self) -> pyo.ConcreteModel:
        """Valida a config do problema e monta o modelo: sets -> parameters -> variables -> expressions -> constraints -> objective."""
        logger.info("Montando modelo a partir de '{}'", self.data.config_dir)
        validate_problem_config(self.data)
        self.sets.attach_to_model(self.model, self.data)
        self.parameters.attach_to_model(self.model, self.data)
        self.variables.attach_to_model(self.model, self.data)
        self.expressions.attach_to_model(self.model, self.data)
        self.constraints.attach_to_model(self.model, self.data)
        self.constraints.apply_enabled(self.model, self.data)
        self.objective.attach_to_model(self.model, self.data)
        self.objective.apply_profile(self.model, self.data)
        logger.info(
            "Modelo montado: {} sets, {} parameters, {} variables, {} constraints",
            len(list(self.model.component_objects(pyo.Set))),
            len(list(self.model.component_objects(pyo.Param))),
            len(list(self.model.component_objects(pyo.Var))),
            len(list(self.model.component_objects(pyo.Constraint))),
        )
        return self.model
