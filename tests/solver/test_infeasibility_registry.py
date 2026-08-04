import optframework.solver.infeasibility  # noqa: F401  (registra gurobi/cplex como side effect)
from optframework.solver.infeasibility.elastic import ElasticRelaxationAnalyzer
from optframework.solver.infeasibility.native import NativeIISAnalyzer
from optframework.solver.infeasibility.registry import get, normalize_solver_name


def test_gurobi_resolves_to_native_analyzer() -> None:
    assert get("gurobi", default=ElasticRelaxationAnalyzer) is NativeIISAnalyzer


def test_gurobi_persistent_resolves_to_native_analyzer() -> None:
    assert get("gurobi_persistent", default=ElasticRelaxationAnalyzer) is NativeIISAnalyzer


def test_cplex_resolves_to_native_analyzer() -> None:
    assert get("cplex", default=ElasticRelaxationAnalyzer) is NativeIISAnalyzer


def test_case_insensitive_lookup() -> None:
    assert get("GUROBI", default=ElasticRelaxationAnalyzer) is NativeIISAnalyzer


def test_unregistered_solver_falls_back_to_default() -> None:
    assert get("appsi_highs", default=ElasticRelaxationAnalyzer) is ElasticRelaxationAnalyzer
    assert get("scip", default=ElasticRelaxationAnalyzer) is ElasticRelaxationAnalyzer


def test_normalize_strips_persistent_and_direct_suffixes() -> None:
    assert normalize_solver_name("gurobi_persistent") == "gurobi"
    assert normalize_solver_name("cplex_direct") == "cplex"
    assert normalize_solver_name("appsi_highs") == "appsi_highs"
