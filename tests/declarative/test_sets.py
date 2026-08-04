from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo

from optframework.declarative.sets import Sets


def test_attach_to_model_creates_sets(tmp_path: Path) -> None:
    (tmp_path / "model_sets.yaml").write_text(
        "sets:\n"
        "  PRODUTOS:\n"
        "    source: data.produtos\n"
        "  PERIODOS:\n"
        "    source: data.periodos\n"
    )
    data = SimpleNamespace(
        config_dir=str(tmp_path), produtos=["p1", "p2"], periodos=[1, 2, 3]
    )
    model = pyo.ConcreteModel()

    Sets().attach_to_model(model, data)

    assert list(model.PRODUTOS) == ["p1", "p2"]
    assert list(model.PERIODOS) == [1, 2, 3]
