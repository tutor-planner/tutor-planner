__author__ = "Matthias Rost <mrost AT inet.tu-berlin.de>"

__all__ = ["PlanningCreator"]

from .base import BasePlanningCreator


class PlanningCreator(BasePlanningCreator):
    """
    The ``PlanningCreator`` for initial planning has no special methods or attributes.
    """

    def __init__(self, target_plan, level=1):
        super().__init__(target_plan, level)
