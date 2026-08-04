from optframework.objective.rules import ObjectiveRules


class FakeObjectives(ObjectiveRules):
    """Rules fake: dois objectives, um deles conta quantas vezes foi chamado (prova cache)."""

    call_count = 0

    def minimizar(self, model: object) -> object:
        FakeObjectives.call_count += 1
        return model.x

    def maximizar(self, model: object) -> object:
        return model.y
