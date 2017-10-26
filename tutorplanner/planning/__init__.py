"""
The ``planning`` package contains the planning steps for initial and rolling
wave planning. It creates a ``PlanningCreator`` and calls the methods to set
the Gurobi variables and constraints. It runs the planner afterwards and saves
the plans.

The implementations of the ``PlanningCreator`` (initial and rolling wave
planning) classes are in :py:mod:`tutorplanner.gurobiinterface`.
"""

__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"
