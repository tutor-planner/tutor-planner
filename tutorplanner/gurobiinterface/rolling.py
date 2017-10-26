__author__ = "Matthias Rost <mrost AT inet.tu-berlin.de>"

__all__ = ["PlanningCreator"]

from gurobipy import LinExpr, GRB, Model

from .base import BasePlanningCreator
from ..input.data import Data
from ..util.settings import DAYS, hours_real, pre_hours_real, TASKS


def past_days(next_day_to_be_planned):
    """
    Return the past day indices.
    """
    return range(1, next_day_to_be_planned)


def coming_days(next_day_to_be_planned):
    """
    Return the next day indices.
    """
    return range(next_day_to_be_planned, 11)


class PlanningCreator(BasePlanningCreator):
    """
    The ``PlanningCreator`` for rolling wave planning has to use the past
    plan.
    """

    def __init__(self, target_plan, past_plan, next_day, level=1):
        super().__init__(target_plan, level)

        self.past_plan = past_plan
        self.next_day = next_day

    def bound_tutor_room_stability(self, tutor_room_stability):
        expr = LinExpr([(1.0, self.same_room[day][hour][tutor][room])
                        for day in DAYS for hour in pre_hours_real(day)
                        for tutor in Data().tutor_by_name.keys() for room in self.rooms])
        self.model.addConstr(expr, GRB.GREATER_EQUAL, tutor_room_stability, "last_bound")
        self.model.update()

    ###
    ###     ROLLING WAVE
    ###

    def create_constraint_bound_task_contingency(self, task_contingency):
        expr = LinExpr()
        for day in coming_days(self.next_day):
            for hour in hours_real(day):
                for tutor in Data().tutor_by_name.keys():
                    for task in TASKS:
                        if self.past_plan[tutor][task][day][hour] != "":
                            expr.addTerms(1.0, self.schedule_entry[tutor][day][hour][task])

        print(" ..final steps")
        constr_name = "boundOnTaskContingency"
        self.model.addConstr(expr, GRB.GREATER_EQUAL, task_contingency, name=constr_name)

    def plugin_obj_maximize_task_contingency(self):
        print(" ..creating objective to maximize Task Contingency")
        expr = LinExpr()
        for day in coming_days(self.next_day):
            for hour in hours_real(day):
                for tutor in Data().tutor_by_name.keys():
                    for task in TASKS:
                        if self.past_plan[tutor][task][day][hour] != "":
                            expr.addTerms(1.0, self.schedule_entry[tutor][day][hour][task])

        print(" ..final steps")
        self.model.setObjective(expr, GRB.MAXIMIZE)

    def plugin_obj_maximize_task_room_contingency(self):
        print(" ..creating objective to maximize Task-Room Contingency")
        expr = LinExpr()
        for day in coming_days(self.next_day):
            for hour in hours_real(day):
                for tutor in Data().tutor_by_name.keys():
                    for task in TASKS:
                        past_room = self.past_plan[tutor][task][day][hour]
                        if past_room != "":
                            expr.addTerms(1.0, self.schedule_entry_rooms[tutor][day][hour][past_room])

        print(" ..final steps")
        self.model.setObjective(expr, GRB.MAXIMIZE)

    def fix_past_assignments(self):
        for tutor in Data().tutor_by_name.keys():
            for day in past_days(self.next_day):
                for hour in hours_real(day):
                    for task in TASKS:
                        if self.past_plan[tutor][task][day][hour] != "":
                            expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])])
                            constr_name = f"fixPastAssignments_{tutor}_{day}_{hour}_{task}"
                            self.model.addConstr(expr, GRB.EQUAL, 1.0, name=constr_name)

    def fix_past_assignments_to_rooms(self):
        for tutor in Data().tutor_by_name.keys():
            for day in past_days(self.next_day):
                for hour in hours_real(day):
                    for task in TASKS:
                        past_room = self.past_plan[tutor][task][day][hour]
                        if past_room != "":
                            expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][past_room])])
                            constr_name = f"fixPastRoomAssignments_{tutor}_{day}_{hour}_{task}"
                            self.model.addConstr(expr, GRB.EQUAL, 1.0, name=constr_name)
