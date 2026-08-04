from optframework.constraints.rules import ConstraintRules


def test_init_stores_data() -> None:
    data = object()

    rules = ConstraintRules(data)

    assert rules.data is data
