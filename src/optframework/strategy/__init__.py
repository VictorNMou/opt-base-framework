from optframework.strategy.milp_strategy import MilpStrategy
from optframework.strategy.registry import register

register("milp", MilpStrategy)
