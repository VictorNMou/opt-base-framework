import pyomo.environ as pyo

from optframework.constraints.orchestrator import Constraints
from optframework.core.problem_data import ProblemData
from optframework.declarative.parameters import Parameters
from optframework.declarative.sets import Sets
from optframework.declarative.variables import Variables
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
        self.constraints: Constraints = Constraints()
        self.objective: Objective = Objective()

    def build(self) -> pyo.ConcreteModel:
        """Monta o modelo na ordem: sets -> parameters -> variables -> constraints -> objective."""
        self.sets.attach_to_model(self.model, self.data)
        self.parameters.attach_to_model(self.model, self.data)
        self.variables.attach_to_model(self.model, self.data)
        self.constraints.attach_to_model(self.model, self.data)
        self.objective.attach_to_model(self.model, self.data)
        return self.model
