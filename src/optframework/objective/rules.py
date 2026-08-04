from optframework.core.problem_data import ProblemData


class ObjectiveRules:
    """Base para as regras de objective de um problema — um método por objective."""

    def __init__(self, data: ProblemData) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data
