import pyomo.environ as pyo
from loguru import logger as loguru_logger

from optframework.logging import configure_logging, logger
from optframework.solver.pyomo_adapter import PyomoAdapter


def _solve_trivial_model() -> None:
    # Dispara um log de dentro do framework (PyomoAdapter.solve) — testa o `disable`/`enable`
    # de fato, já que ele filtra pelo módulo de origem da chamada, não de quem importou `logger`.
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 10))
    model.obj = pyo.Objective(expr=model.x, sense=pyo.maximize)
    PyomoAdapter().solve(model)


def test_framework_logs_disabled_by_default() -> None:
    sink: list[str] = []
    handler_id = loguru_logger.add(sink.append, format="{message}")
    try:
        _solve_trivial_model()
    finally:
        loguru_logger.remove(handler_id)

    assert sink == []


def test_configure_logging_enables_framework_logs_and_writes_to_sink() -> None:
    sink: list[str] = []
    handler_id = configure_logging(sink=sink.append, colorize=False)
    try:
        _solve_trivial_model()
    finally:
        loguru_logger.remove(handler_id)
        loguru_logger.disable("optframework")

    assert any("Solve" in line for line in sink)


def test_configure_logging_respects_level() -> None:
    sink: list[str] = []
    handler_id = configure_logging(level="ERROR", sink=sink.append, colorize=False)
    try:
        _solve_trivial_model()
    finally:
        loguru_logger.remove(handler_id)
        loguru_logger.disable("optframework")

    assert sink == []


def test_configure_logging_returns_removable_handler_id() -> None:
    handler_id = configure_logging(sink=lambda _msg: None)
    try:
        assert isinstance(handler_id, int)
    finally:
        loguru_logger.remove(handler_id)
        loguru_logger.disable("optframework")


def test_logger_is_the_shared_loguru_instance() -> None:
    assert logger is loguru_logger
