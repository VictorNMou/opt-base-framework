class FakeObjectives:
    """Rules fake: dois objectives, um deles conta quantas vezes foi chamado (prova cache)."""

    call_count = 0

    def __init__(self, data: object) -> None:
        """Guarda os dados do problema; disponíveis a cada método via self.data."""
        self.data = data

    def minimizar(self, model: object) -> object:
        FakeObjectives.call_count += 1
        return model.x

    def maximizar(self, model: object) -> object:
        return model.y
