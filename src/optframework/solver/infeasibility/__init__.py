from optframework.solver.infeasibility.native import NativeIISAnalyzer
from optframework.solver.infeasibility.registry import register

register("gurobi", NativeIISAnalyzer)
register("cplex", NativeIISAnalyzer)
