from optframework.strategy.milp_strategy import MilpStrategy
from optframework.strategy.registry import register

register("milp", MilpStrategy)
register("lp", MilpStrategy)  # LP é caso particular de MILP (zero variáveis inteiras/binárias)
