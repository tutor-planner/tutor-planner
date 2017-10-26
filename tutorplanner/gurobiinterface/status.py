__author__ = "Matthias Rost <mrost AT inet.tu-berlin.de>"

__all__ = ["GurobiStatus"]

from gurobipy import GRB


class GurobiStatus:
    """
    Wrapper for evaluating MIP results
    """

    #: Model is loaded, but no solution information is available.
    LOADED = 1
    #: Model was solved to optimality (subject to tolerances), and an optimal solution is available.
    OPTIMAL = 2
    #: Model was proven to be infeasible.
    INFEASIBLE = 3
    #: Model was proven to be either infeasible or unbounded. To obtain a more definitive conclusion,
    #: set the DualReductions parameter to 0 and reoptimize.
    INF_OR_UNBD = 4
    #: Model was proven to be unbounded. Important note: an unbounded status indicates the presence of
    #: an unbounded ray that allows the objective to improve without limit. It says nothing about whether
    #: the model has a feasible solution. If you require information on feasibility, you should set the
    #: objective to zero and reoptimize.
    UNBOUNDED = 5
    #: Optimal objective for model was proven to be worse than the value specified in the Cutoff parameter.
    #: No solution information is available.
    CUTOFF = 6
    #: Optimization terminated because the total number of simplex iterations performed exceeded the value
    #: specified in the IterationLimit parameter, or because the total number of barrier iterations exceeded
    #: the value specified in the BarIterLimit parameter.
    ITERATION_LIMIT = 7
    #: Optimization terminated because the total number of branch-and-cut nodes explored exceeded the value
    #: specified in the NodeLimit parameter.
    NODE_LIMIT = 8
    #: Optimization terminated because the time expended exceeded the value specified in the TimeLimit parameter.
    TIME_LIMIT = 9
    #: Optimization terminated because the number of solutions found reached the value specified in the
    #: SolutionLimit parameter.
    SOLUTION_LIMIT = 10
    #: Optimization was terminated by the user.
    INTERRUPTED = 11
    #: Optimization was terminated due to unrecoverable numerical difficulties.
    NUMERIC = 12
    #: Unable to satisfy optimality tolerances; a sub-optimal solution is available.
    SUBOPTIMAL = 13
    #: A non-blocking optimization call was made (by setting the NonBlocking parameter to 1 in a
    #: Gurobi Compute Server environment), but the associated optimization run is not yet complete.
    IN_PROGRESS = 14

    def __init__(self, sol_count=0, status=1, gap=GRB.INFINITY, objective=-1):
        self.sol_count = sol_count
        self.status = status
        self.gap = gap
        self.objective = objective

    def get_objective(self):
        return self.objective

    def is_feasible(self):
        result = self.sol_count > 0
        if self.status == self.INFEASIBLE:
            result = False
        if self.status == self.INF_OR_UNBD:
            result = False
        if self.status == self.UNBOUNDED:
            result = False
        if self.status == self.NUMERIC:
            result = False
        if self.gap == GRB.INFINITY:
            result = False
        return result

    def is_optimal(self):
        return self.status == self.OPTIMAL
