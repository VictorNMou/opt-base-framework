from optframework.core.problem_data import ProblemData


class ConstraintRules:
    """Base para as regras de constraint de um problema — um método por constraint."""

    def __init__(self, data: ProblemData) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data
