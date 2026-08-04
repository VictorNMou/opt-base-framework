import pyomo.environ as pyo
import pytest

from optframework.constraints.rules import ConstraintRules


def test_build_rule_not_implemented() -> None:
    rules = ConstraintRules(preprocessed={})

    with pytest.raises(NotImplementedError):
        rules.build_rule(pyo.ConcreteModel(), "capacidade")
