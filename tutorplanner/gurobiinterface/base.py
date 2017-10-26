__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = ["BasePlanningCreator"]

import itertools
import re

from gurobipy import LinExpr, GRB, Model

from . import status
from ..input.data import Data
from ..input.plan import get_empty_plan
from ..util.converter import date_to_day_index
from ..util.settings import settings, get_room_info, DAYS, hours_real, pre_hours_real, \
    TASKS, TUTORIUM, UEBUNG_MAR, UEBUNG_TEL, KONTROLLE


class BasePlanningCreator:
    """
    Common base of initial and rolling wave planning.
    """

    def __init__(self, target_plan, level=1):
        self.name = f"Level_{level}"

        self.max_slack = 0.6
        self.max_overload = 1.2
        self.target_plan = target_plan
        self.status = None
        self.level = level
        self.model = Model(f"LevelPlanner_{level}")

        self.specific_working_hours = settings.specific_working_hours._or({})()
        self.forbidden_tasks = settings.forbidden_tasks._or({})()

        self.pool_rooms = Data().get_exercise_rooms()
        self.pool_rooms.remove("TEL 103")
        self.tutorial_rooms = list(Data().room_by_type["tutorial"].keys())
        self.rooms = self.pool_rooms + self.tutorial_rooms + ["TEL 109"]
        self.mip_gap = 0.01

        # variables
        self.schedule_entry = None
        self.schedule_entry_rooms = None
        self.plan_deviation = None

        # custom constraints
        self.compute_deviation_from_plan = None

        # level 2
        self.ws_constraints = None
        self.var_work_spread = None

        # level 3
        self.mh_constraints = None
        self.var_minimal_happiness = None

        # level 5
        self.mar_tel_hopping = None
        self.mth_cons = None

        # other levels might be missing here; no time :|

    def create_model_without_rooms(self):
        self.status = None
        self.create_basic_variables()
        self.model.update()
        self.create_basic_constraints()
        self.model.update()

    def extend_model_with_room_support(self):
        self.create_room_assignment_variables()
        self.model.update()
        self.create_task_to_room_constraints()

    def solve_integer_program(self):
        self.model.setParam('MIPGap', self.mip_gap)
        self.model.optimize()
        solution_count = self.model.getAttr("solCount")
        objective_value = -1
        if solution_count > 0:
            objective_value = self.model.getAttr("ObjVal")
        self.status = status.GurobiStatus(solution_count,
                                          self.model.getAttr("Status"),
                                          self.model.getAttr("MIPGap"),
                                          objective_value)

        if not self.status.is_feasible():
            print("The model was not feasible. Generating irreducible linear program..")
            self.model.computeIIS()
            self.model.write("foo.ilp")
            print("The irreducible linear program was written to foo.ilp, cheers.")

        return self.status

    ###
    ###     CREATING MAIN VARIABLES
    ###

    def create_basic_variables(self):
        print("..constructing Variables")
        # tutor -> day -> time -> task
        self.schedule_entry = {}

        for tutor in Data().tutor_by_name.keys():
            self.schedule_entry[tutor] = {}
            for day in DAYS:
                self.schedule_entry[tutor][day] = {}
                for hour in hours_real(day):
                    self.schedule_entry[tutor][day][hour] = {}
                    for task in TASKS:
                        variable_id = f"schedule_{tutor}_{day}_{hour}_{task}"
                        self.schedule_entry[tutor][day][hour][task] = self.model.addVar(
                            lb=0.0, ub=1.0, obj=0.0, vtype=GRB.BINARY, name=variable_id)

    def create_room_assignment_variables(self):
        self.schedule_entry_rooms = {}
        for tutor in Data().tutor_by_name.keys():
            self.schedule_entry_rooms[tutor] = {}
            for day in DAYS:
                self.schedule_entry_rooms[tutor][day] = {}
                for hour in hours_real(day):
                    self.schedule_entry_rooms[tutor][day][hour] = {}
                    for room in self.rooms:
                        variable_id = f"schedule_{tutor}_{day}_{hour}_{room}"
                        self.schedule_entry_rooms[tutor][day][hour][room] = self.model.addVar(
                            lb=0.0, ub=1.0, obj=0.0, vtype=GRB.BINARY, name=variable_id)

    ###
    ###     CREATING BASIC CONSTRAINTS -- BEGIN
    ###

    def create_basic_constraints(self):
        print("..constructing Constraints")
        self.create_constraint_unique_task_at_a_given_time()
        self.create_constraint_tutor_has_time_for_task()
        self.create_constraint_tasks_are_bounded_by_targeted_plan()
        self.create_constraint_concurrent_tutorials_are_bounded_by_number_of_rooms()
        # self.createConstraint_EachTutorIsSomehowHappy()  # TODO
        self.create_constraint_work_is_shared_fairly()
        self.create_constraint_tutors_have_pauses()
        print(".. Constraints ready.")

    def create_constraint_unique_task_at_a_given_time(self):
        print("  ..constructing UniqueTaskAtAGivenTime")
        for tutor in Data().tutor_by_name.keys():
            for day in DAYS:
                for hour in hours_real(day):
                    expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task]) for task in TASKS])
                    constr_name = f"UniqueTaskAtAGivenTime_{tutor}_{day}_{hour}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

    def create_constraint_tutor_has_time_for_task(self):
        print("  ..constructing TutorHasTimeForTask")
        # this is equivalent to forbidding any assignments at times at which she does not have time
        for tutor in Data().tutor_by_name.keys():
            expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                            for day in DAYS for hour in hours_real(day)
                            for task in TASKS if Data().availability[tutor][day][hour] < 1])
            constr_name = f"TutorHasTimeForTask_{tutor}"
            if tutor in self.forbidden_tasks:
                print(f"Tutor {tutor} has forbidden TASKS {self.forbidden_tasks[tutor]}")
                expr2 = LinExpr([(1.0, self.schedule_entry[tutor][date_to_day_index(date)][hour][task])
                                 for task in self.forbidden_tasks[tutor]
                                 for date in self.forbidden_tasks[tutor][task]
                                 for hour in hours_real(date_to_day_index(date))])
                print(expr2)
                expr.add(expr2)
            self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)

    def create_constraint_tasks_are_bounded_by_targeted_plan(self):
        print("  ..constructing TasksAreBoundedByTargetedPlan")
        for day in DAYS:
            for hour in hours_real(day):
                for task in TASKS:
                    expr = LinExpr(
                        [(1.0, self.schedule_entry[tutor][day][hour][task]) for tutor in Data().tutor_by_name.keys()])
                    constr_name = f"TasksAreBoundedByTargetedPlan_{day}_{hour}_{task}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, self.target_plan[task][day][hour], name=constr_name)

    def create_constraint_concurrent_tutorials_are_bounded_by_number_of_rooms(self):
        print("  ..constructing ConcurrentTutorialsAreBoundedByNumberOfRooms")
        for day in DAYS:
            for hour in hours_real(day):
                expr = LinExpr(
                    [(1.0, self.schedule_entry[tutor][day][hour][TUTORIUM]) for tutor in Data().tutor_by_name])
                constr_name = f"ConcurrentTutorialsAreBoundedByNumberOfRooms_{day}_{hour}"
                self.model.addConstr(expr, GRB.LESS_EQUAL, Data().get_number_of_tutorial_rooms(day, hour),
                                     name=constr_name)

    def create_constraint_work_is_shared_fairly(self):
        print("  ..constructing WorkIsSharedFairly")
        # working hour bounds for both weeks
        for tutor in Data().tutor_by_name.keys():
            if tutor in self.specific_working_hours:
                expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                                for day in DAYS for hour in hours_real(day) for task in TASKS])
                specific_working_hours = self.specific_working_hours[tutor]["total"]
                min = specific_working_hours["min"]
                max = specific_working_hours["max"]
                constr_name = f"WorkIsSharedFairly_Over2Weeks_special_{tutor}"
                self.model.addConstr(expr, GRB.GREATER_EQUAL, min, name=constr_name + "_lower")
                self.model.addConstr(expr, GRB.LESS_EQUAL, max, name=constr_name + "_upper")
            else:
                expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                                for day in DAYS for hour in hours_real(day) for task in TASKS])
                constr_name = f"WorkIsSharedFairly_Over2Weeks_{tutor}"
                two_weeks_working_hours = Data().tutor_by_name[tutor].monthly_work_hours / 2.0
                self.model.addConstr(expr, GRB.GREATER_EQUAL, two_weeks_working_hours * self.max_slack,
                                     name=constr_name + "_lower")
                self.model.addConstr(expr, GRB.LESS_EQUAL, two_weeks_working_hours, name=constr_name + "_upper")
        # working hour bounds for first week
        for tutor in Data().tutor_by_name.keys():
            expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                            for day in range(1, 6) for hour in hours_real(day) for task in TASKS])
            if tutor in self.specific_working_hours:
                specific_working_hours = self.specific_working_hours[tutor]["first_week"]
                min = specific_working_hours["min"]
                max = specific_working_hours["max"]
                constr_name = f"WorkIsSharedFairly_OverFirst_{tutor}"
                self.model.addConstr(expr, GRB.GREATER_EQUAL, min, name=constr_name + "_lower")
                self.model.addConstr(expr, GRB.LESS_EQUAL, max, name=constr_name + "_upper")
            else:
                constr_name = f"WorkIsSharedFairly_OverFirst_{tutor}"
                weekly_working_hours = Data().tutor_by_name[tutor].monthly_work_hours / 4.0
                self.model.addConstr(expr, GRB.GREATER_EQUAL, weekly_working_hours * self.max_slack,
                                     name=constr_name + "_lower")
                self.model.addConstr(expr, GRB.LESS_EQUAL, weekly_working_hours * self.max_overload,
                                     name=constr_name + "_upper")
        # working hour bounds for second week
        for tutor in Data().tutor_by_name.keys():
            expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                            for day in range(6, 11, 1) for hour in hours_real(day) for task in TASKS])
            if tutor in self.specific_working_hours:
                specific_working_hours = self.specific_working_hours[tutor]["second_week"]
                min = specific_working_hours["min"]
                max = specific_working_hours["max"]
                constr_name = f"WorkIsSharedFairly_OverSecond_{tutor}"
                self.model.addConstr(expr, GRB.GREATER_EQUAL, min, name=constr_name + "_lower")
                self.model.addConstr(expr, GRB.LESS_EQUAL, max, name=constr_name + "_upper")
            else:
                constr_name = f"WorkIsSharedFairly_OverSecond_{tutor}"
                weekly_working_hours = Data().tutor_by_name[tutor].monthly_work_hours / 4.0
                self.model.addConstr(expr, GRB.GREATER_EQUAL, weekly_working_hours * self.max_slack,
                                     name=constr_name + "_lower")
                self.model.addConstr(expr, GRB.LESS_EQUAL, weekly_working_hours * self.max_overload,
                                     name=constr_name + "_upper")

    def create_constraint_tutors_have_pauses(self):
        print("  ..constructing TutorsHavePauses")
        for tutor in Data().tutor_by_name.keys():
            max_work_overall = Data().tutor_by_name[tutor].max_hours_without_break
            for day in DAYS:
                hours = hours_real(day)
                if max_work_overall > len(hours):
                    continue
                for hour in hours[:-max_work_overall]:
                    expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + incr][task])
                                    for incr in range(max_work_overall + 1) for task in TASKS])
                    constr_name = f"TutorsHavePauses_{tutor}_{day}_{hour}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, max_work_overall, name=constr_name)

        for tutor in Data().tutor_by_name.keys():
            max_work_tuts = Data().tutor_by_name[tutor].max_tutorials_without_break
            for day in DAYS:
                hours = hours_real(day)
                if max_work_tuts > len(hours):
                    continue
                for hour in hours[:-max_work_tuts]:
                    expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + incr][TUTORIUM])
                                    for incr in range(max_work_tuts + 1)])
                    constr_name = f"TutorsHavePauses_{tutor}_{day}_{hour}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, max_work_tuts, name=constr_name)

    ###
    ###     CREATING BASIC CONSTRAINTS -- END
    ###

    ###
    ###     CREATING ROOM CONSTRAINTS -- BEGIN
    ###

    def create_task_to_room_constraints(self):
        self.construct_variables_and_constraints_on_external_room_usages()
        self.create_constraint_equalized_split_of_tutors_for_pools()
        self.create_mapping_between_normal_schedule_and_rooms()
        self.no_overlapping_tutorial_room_bookings()
        self.no_room_bookings_when_not_available()

    def construct_variables_and_constraints_on_external_room_usages(self):
        self.external_room_usage = {}
        for day in DAYS:
            self.external_room_usage[day] = {}
            for room in Data().rooms_external:
                variable_id = f"externalRoomUsage_{day}_{room}"

                self.external_room_usage[day][room] = self.model.addVar(
                    lb=0.0, ub=1.0, obj=0.0, vtype=GRB.BINARY, name=variable_id)

        self.model.update()

        for day in DAYS:
            for hour in hours_real(day):
                for room in Data().rooms_external:

                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room])
                                    for tutor in Data().tutor_by_name.keys()])
                    expr2 = LinExpr([(-1.0, self.external_room_usage[day][room])])
                    expr.add(expr2)

                    constr_name = f"computeExternalDay_{day}_{hour}_{room}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, 0.0, name=constr_name)

    def create_constraint_equalized_split_of_tutors_for_pools(self):
        pool_locations = ["MAR", "TEL"]

        self.model.update()

        self.pool_slack = {}
        for day in DAYS:
            self.pool_slack[day] = {}
            for hour in hours_real(day):
                self.pool_slack[day][hour] = {}
                for location in pool_locations:
                    variable_id = f"poolSlack_{day}_{hour}_{location}"
                    self.pool_slack[day][hour][location] = self.model.addVar(
                        lb=-1.0, ub=1.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)

        self.model.update()

        for day, values in self.pool_slack.items():
            for hour, values2 in values.items():
                for location, values3 in values2.items():
                    slack_variable = values3
                    if "TEL" in location:
                        tel106_rooms = [x for x in Data().bookings_pools[day][hour] if x.startswith("TEL 106")]
                        tel206_rooms = [x for x in Data().bookings_pools[day][hour] if x.startswith("TEL 206")]
                        tel_rooms = tel106_rooms + tel206_rooms
                        if len(tel_rooms) > 1:
                            for room_a, room_b in itertools.combinations(tel_rooms, 2):
                                variable_id = f"poolSlack_{day}_{hour}_{room_a}_{room_b}"
                                slack_variable = self.model.addVar(
                                    lb=-1.0, ub=1.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)
                                expr = LinExpr()
                                expr.addTerms(1.0, slack_variable)
                                expr_room_a = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room_a])
                                                       for tutor in Data().tutor_by_name.keys()])
                                expr_room_b = LinExpr([(-1.0, self.schedule_entry_rooms[tutor][day][hour][room_b])
                                                       for tutor in Data().tutor_by_name.keys()])
                                expr.add(expr_room_a)
                                expr.add(expr_room_b)
                                constr_name = f"equalizedUsage_{room_a}_{room_b}_{day}_{hour}"
                                self.model.update()
                                self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)
                    elif "MAR" in location:
                        if "MAR 6.001" in Data().bookings_pools[day][hour] \
                                and "MAR 6.057" in Data().bookings_pools[day][hour]:
                            expr = LinExpr()
                            expr.addTerms(1.0, slack_variable)
                            expr_room_a = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour]["MAR 6.001"])
                                                   for tutor in Data().tutor_by_name.keys()])
                            expr_room_b = LinExpr([(-1.0, self.schedule_entry_rooms[tutor][day][hour]["MAR 6.057"])
                                                   for tutor in Data().tutor_by_name.keys()])
                            expr.add(expr_room_a)
                            expr.add(expr_room_b)
                            constr_name = f"equalizedUsage_{location}_{day}_{hour}"
                            self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)
                    else:
                        print("unhandled " + location)

    def create_mapping_between_normal_schedule_and_rooms(self):
        # no two rooms at a given time for tutor
        for tutor in Data().tutor_by_name.keys():
            for day in DAYS:
                for hour in hours_real(day):
                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room]) for room in self.rooms])
                    constr_name = f"UniqueRoomAtAGivenTime_{tutor}_{day}_{hour}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

        # if in the task planning a tutor is used for some task, then one of the rooms must be selected accordingly
        for tutor in Data().tutor_by_name.keys():
            for day in DAYS:
                for hour in hours_real(day):

                    # for POOLS - TEL
                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][poolRoom])
                                    for poolRoom in self.pool_rooms if ("TEL" in poolRoom and "109" not in poolRoom)])
                    constr_name = f"Room-Task-Enforcement-Pools-TEL_{tutor}_{day}_{hour}"
                    expr.addTerms(-1.0, self.schedule_entry[tutor][day][hour][UEBUNG_TEL])
                    self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)

                    # for POOLS - MAR
                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][poolRoom])
                                    for poolRoom in self.pool_rooms if "MAR" in poolRoom])
                    constr_name = f"Room-Task-Enforcement-Pools-MAR_{tutor}_{day}_{hour}"
                    expr.addTerms(-1.0, self.schedule_entry[tutor][day][hour][UEBUNG_MAR])
                    self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)

                    # for KONTROLLE
                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour]["TEL 109"])])
                    constr_name = f"Room-Task-Enforcement-Kontrolle_{tutor}_{day}_{hour}"
                    expr.addTerms(-1.0, self.schedule_entry[tutor][day][hour][KONTROLLE])
                    self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)

                    # for POOLS - TEL
                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][tutRoom])
                                    for tutRoom in self.tutorial_rooms])
                    constr_name = f"Room-Task-Enforcement-Pools-TEL_{tutor}_{day}_{hour}"
                    expr.addTerms(-1.0, self.schedule_entry[tutor][day][hour][TUTORIUM])
                    self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)

    def no_overlapping_tutorial_room_bookings(self):
        for day in DAYS:
            for hour in hours_real(day):
                for room in self.tutorial_rooms:
                    expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room])
                                    for tutor in Data().tutor_by_name.keys()])
                    constr_name = f"UniqueAssignmentToTutorialRooms_{room}_{day}_{hour}"
                    self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

    def no_room_bookings_when_not_available(self):
        for day in DAYS:
            for hour in hours_real(day):
                for room in self.rooms:
                    if room == "TEL 103" or room == "TEL 109":
                        # WE DO NOT CONSIDER TEL 103 / 109
                        continue
                    if "TEL" in room or room == "MAR 6.001" or room == "MAR 6.057":
                        # if it is a pool room, we get the reservations from ..
                        reservations = Data().bookings_pools
                        if room not in reservations[day][hour]:
                            expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room])
                                            for tutor in Data().tutor_by_name.keys()])
                            constr_name = f"NonBookedRoom_{room}_{day}_{hour}"
                            self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)
                    else:
                        reservations = Data().bookings_tutorials
                        if room not in reservations[day][hour]:
                            expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room])
                                            for tutor in Data().tutor_by_name.keys()])
                            constr_name = f"NonBookedRoom_{room}_{day}_{hour}"
                            self.model.addConstr(expr, GRB.EQUAL, 0.0, name=constr_name)

    ###
    ###     CREATING ROOM CONSTRAINTS -- END
    ###

    ###
    ###     LEVEL 1:
    ###

    def plugin_obj_minimize_deviation_from_plan(self):
        print(" ..creating objective to minimize the deviation from the plan")

        if self.plan_deviation is None:
            print("   ..creating the appropriate variables")
            self.plan_deviation = {}
            for day in DAYS:
                self.plan_deviation[day] = {}
                for hour in hours_real(day):
                    self.plan_deviation[day][hour] = {}
                    for task in TASKS:
                        variable_id = f"planDeviation_{day}_{hour}_{task}"
                        self.plan_deviation[day][hour][task] = self.model.addVar(
                            lb=-0.0, ub=20.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)
            self.model.update()
        else:
            print("   ..appropriate variables were already created")

        if self.compute_deviation_from_plan is None:
            print("   ..creating the appropriate variables")
            self.compute_deviation_from_plan = []
            for day in DAYS:
                for hour in hours_real(day):
                    for task in TASKS:
                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                                        for tutor in Data().tutor_by_name.keys()])
                        expr.addTerms(1.0, self.plan_deviation[day][hour][task])
                        constr_name = f"computeLocalDeviationFromTargetPlan_{day}_{hour}_{task}"
                        self.compute_deviation_from_plan.append(self.model.addConstr(
                            expr, GRB.EQUAL, self.target_plan[task][day][hour], name=constr_name))

        print(" ..setting the objective function")
        expr = LinExpr([(1.0, self.plan_deviation[day][hour][task])
                        for day in DAYS for hour in hours_real(day) for task in TASKS])
        self.model.setObjective(expr, GRB.MINIMIZE)

    ###
    ###     LEVEL 2:
    ###

    def plugin_constraint_bound_maximal_deviation_from_target_plan(self, max_deviation):
        print("  ..constructing boundMaximalDeviationFromTargetPlan")
        for day in DAYS:
            for hour in hours_real(day):
                for task in TASKS:
                    expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][task])
                                    for tutor in Data().tutor_by_name.keys()])
                    constr_name = f"boundMaximalDeviationFromTargetPlan_{day}_{hour}_{task}"
                    self.model.addConstr(expr, GRB.GREATER_EQUAL, self.target_plan[task][day][hour] - max_deviation, name=constr_name)

    ###
    ###     LEVEL 3:
    ###

    def construct_work_spread_variables(self):
        if self.var_work_spread is None:
            self.var_work_spread = {}
            variable_id = "min_rel_work"
            self.var_work_spread["min"] = self.model.addVar(
                lb=0.0, ub=1.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)
            variable_id = "max_rel_work"
            self.var_work_spread["max"] = self.model.addVar(
                lb=0.0, ub=1.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)
            self.model.update()

    def construct_work_spread_constraints(self):
        if self.ws_constraints is None:
            self.ws_constraints = []
            for tutor in Data().tutor_by_name.keys():
                if tutor in self.specific_working_hours:
                    expected_work_time = self.specific_working_hours[tutor]["total"]["max"]
                else:
                    expected_work_time = Data().tutor_by_name[tutor].monthly_work_hours / 2.0
                expr = LinExpr([(1.0 / expected_work_time, self.schedule_entry[tutor][day][hour][task])
                                for day in DAYS for hour in hours_real(day) for task in TASKS])
                constr_name = f"bound_work_spread_from_above_{tutor}"
                self.model.addConstr(expr, GRB.LESS_EQUAL, self.var_work_spread["max"], name=constr_name)
                constr_name = f"bound_work_spread_from_below_{tutor}"
                self.model.addConstr(expr, GRB.GREATER_EQUAL, self.var_work_spread["min"], name=constr_name)

    def plugin_obj_minimize_work_spread(self):
        self.construct_work_spread_variables()
        self.construct_work_spread_constraints()
        expr = LinExpr()
        expr.addTerms(1.0, self.var_work_spread["max"])
        expr.addTerms(-1.0, self.var_work_spread["min"])
        self.model.setObjective(expr, GRB.MINIMIZE)

        self.set_relative_mip_gap(0.01)
        self.set_time_limit(settings.optimization_parameters.time_limits.short._or(20)())

    def bound_maximal_work_spread(self, maximal_work_spread):
        self.construct_work_spread_variables()
        self.construct_work_spread_constraints()
        expr = LinExpr()
        expr.addTerms(1.0, self.var_work_spread["max"])
        expr.addTerms(-1.0, self.var_work_spread["min"])
        self.model.addConstr(expr, GRB.LESS_EQUAL, maximal_work_spread, "bound_maximal_work_spread")

    ###
    ###     LEVEL 4
    ###

    def construct_minimal_happiness_variables(self):
        if self.var_minimal_happiness is None:
            self.var_minimal_happiness = self.model.addVar(
                lb=0.9, ub=3.0, obj=0.0, vtype=GRB.CONTINUOUS, name="minimal_tutor_happiness")
            self.model.update()

    def construct_minimal_happiness_constraints(self, max_workload):
        if self.mh_constraints is None:
            self.mh_constraints = []

            for tutor in Data().tutor_by_name.keys():
                expr = LinExpr([(Data().availability[tutor][day][hour], self.schedule_entry[tutor][day][hour][task])
                                for day in DAYS for hour in hours_real(day) for task in TASKS])
                if tutor in self.specific_working_hours:
                    two_weeks_working_hours = self.specific_working_hours[tutor]["total"]["max"]
                else:
                    two_weeks_working_hours = Data().tutor_by_name[tutor].monthly_work_hours / 2.0
                expr.addTerms(-1.0 * two_weeks_working_hours * max_workload, self.var_minimal_happiness)
                self.mh_constraints.append(
                    self.model.addConstr(expr, GRB.GREATER_EQUAL, 0, name=f"bound_minimal_happiness_{tutor}"))

    def plugin_obj_maximize_min_happiness(self, max_workload):
        self.construct_minimal_happiness_variables()
        self.construct_minimal_happiness_constraints(max_workload)
        expr = LinExpr(self.var_minimal_happiness)
        self.model.setObjective(expr, GRB.MAXIMIZE)

        self.set_relative_mip_gap(0.01)
        self.set_time_limit(settings.optimization_parameters.time_limits.short._or(20)())

    def bound_min_happiness(self, max_workload, minimal_happiness):
        self.construct_minimal_happiness_variables()
        self.construct_minimal_happiness_constraints(max_workload)
        expr = LinExpr(self.var_minimal_happiness)
        self.mh_constraints.append(
            self.model.addConstr(expr, GRB.GREATER_EQUAL, minimal_happiness, "bound_min_happiness"))

    ###
    ###     LEVEL 5
    ###

    def plugin_obj_maximize_cube_happiness(self):
        obj = LinExpr([
            (Data().availability[tutor][day][hour]**3, self.schedule_entry[tutor][day][hour][task])
            for tutor in Data().tutor_by_name.keys()
            for day in DAYS
            for hour in hours_real(day)
            for task in TASKS])
        self.model.setObjective(obj, GRB.MAXIMIZE)
        self.set_relative_mip_gap(0.01)
        self.set_time_limit(settings.optimization_parameters.time_limits.short._or(20)())

    def bound_cube_happiness_from_below(self, happiness_value):
        cube_happiness = LinExpr([
            (Data().availability[tutor][day][hour]**3, self.schedule_entry[tutor][day][hour][task])
            for tutor in Data().tutor_by_name.keys()
            for day in DAYS
            for hour in hours_real(day)
            for task in TASKS])
        self.model.addConstr(cube_happiness, GRB.GREATER_EQUAL, happiness_value)

    ###
    ###     LEVEL 6
    ###

    def create_mar_tel_hopping_variables(self):
        if self.mar_tel_hopping is None:
            self.mar_tel_hopping = {}
            for day in DAYS:
                self.mar_tel_hopping[day] = {}
                for hour in hours_real(day):
                    self.mar_tel_hopping[day][hour] = {}
                    for tutor in Data().tutor_by_name.keys():
                        variable_id = f"changeMAR_TEL_{day}_{hour}_{tutor}"
                        self.mar_tel_hopping[day][hour][tutor] = self.model.addVar(
                            lb=0.0, ub=1.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)

            self.model.update()

    def create_mar_tel_hopping_constraints(self):
        self.create_mar_tel_hopping_variables()
        if self.mth_cons is None:
            self.mth_cons = []
            for day in DAYS:
                for hour in pre_hours_real(day):
                    for tutor in Data().tutor_by_name.keys():
                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][UEBUNG_MAR])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][UEBUNG_TEL])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan1_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][UEBUNG_MAR])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][KONTROLLE])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan2_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][UEBUNG_TEL])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][UEBUNG_MAR])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan3_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][KONTROLLE])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][UEBUNG_MAR])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan4_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][KONTROLLE])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][TUTORIUM])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan5_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][UEBUNG_TEL])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][TUTORIUM])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan6_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][UEBUNG_MAR])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][TUTORIUM])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan7_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][TUTORIUM])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][UEBUNG_TEL])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan8_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][TUTORIUM])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][UEBUNG_MAR])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan9_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(1.0, self.schedule_entry[tutor][day][hour][TUTORIUM])])
                        expr2 = LinExpr([(1.0, self.schedule_entry[tutor][day][hour + 1][KONTROLLE])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.mar_tel_hopping[day][hour][tutor])
                        constr_name = f"computeLocalDeviationFromTargetPlan10_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

    def plugin_obj_minimize_mar_tel_hopping(self):
        print(" ..creating objective to minimize Mar Tel hoppings")
        self.create_mar_tel_hopping_variables()
        self.create_mar_tel_hopping_constraints()
        print(" ..final steps")
        expr = LinExpr([(1.0, self.mar_tel_hopping[day][hour][tutor])
                        for day in DAYS for hour in hours_real(day) for tutor in Data().tutor_by_name.keys()])
        self.model.setObjective(expr, GRB.MINIMIZE)
        self.set_relative_mip_gap(0.01)
        self.set_time_limit(settings.optimization_parameters.time_limits.short._or(20)())

    def create_constraint_minimal_mar_tel_hopping(self, max_number_of_mar_tel_hoppings):
        expr = LinExpr([(1.0, self.mar_tel_hopping[day][hour][tutor])
                        for day in DAYS for hour in hours_real(day) for tutor in Data().tutor_by_name.keys()])
        constr_name = "boundMaximalTEL_MAR_Hopping"
        self.model.addConstr(expr, GRB.LESS_EQUAL, max_number_of_mar_tel_hoppings, name=constr_name)

    ###
    ###     LEVEL 7
    ###

    def get_priorities_of_rooms(self):
        external_regex = "MAR 4.033|MAR 6.004|MAR 6.011"
        best_regex = "MAR .*|FH .*"
        others_regex = ".*"
        external_matcher = re.compile(external_regex)
        best_matcher = re.compile(best_regex)
        other_matcher = re.compile(others_regex)

        result = {}
        for room_name in self.rooms:
            if get_room_info(room_name)["type"] != "tutorial":
                result[room_name] = 0
            elif external_matcher.match(room_name):
                print(f"{room_name} is external")
                result[room_name] = 1000.0 * get_room_info(room_name)["capacity"]
            elif best_matcher.match(room_name):
                print(f"{room_name} is best")
                result[room_name] = 1000.0 * (1000.0 * get_room_info(room_name)["capacity"])
            elif other_matcher.match(room_name):
                print(f"{room_name} is other")
                result[room_name] = get_room_info(room_name)["capacity"]
            else:
                raise Exception("Could not determine priority")
        return result

    def plugin_objective_select_best_rooms(self):
        priorities_of_rooms = self.get_priorities_of_rooms()
        expr = LinExpr([(priorities_of_rooms[room], self.schedule_entry_rooms[tutor][day][hour][room])
                        for tutor in Data().tutor_by_name.keys()
                        for day in DAYS for hour in hours_real(day) for room in self.rooms])
        self.model.setObjective(expr, GRB.MAXIMIZE)
        self.set_relative_mip_gap(0.01)
        self.set_time_limit(settings.optimization_parameters.time_limits.short._or(20)())

    def bound_best_rooms_from_below(self, prio_sum):
        priorities_of_rooms = self.get_priorities_of_rooms()
        expr = LinExpr([(priorities_of_rooms[room], self.schedule_entry_rooms[tutor][day][hour][room])
                        for tutor in Data().tutor_by_name.keys()
                        for day in DAYS for hour in hours_real(day) for room in self.rooms])
        self.model.addConstr(expr, GRB.GREATER_EQUAL, prio_sum)

    ###
    ###     LEVEL 8
    ###

    def plugin_obj_maximize_tutor_room_stability(self):
        print(" ..creating objective to minimize the room hoppings")
        self.same_room = {}
        for day in DAYS:
            self.same_room[day] = {}
            for hour in pre_hours_real(day):
                self.same_room[day][hour] = {}
                for tutor in Data().tutor_by_name.keys():
                    self.same_room[day][hour][tutor] = {}
                    for room in self.rooms:
                        variable_id = f"changeMAR_TEL_{day}_{hour}_{tutor}_{room}"
                        self.same_room[day][hour][tutor][room] = self.model.addVar(
                            lb=0.0, ub=1.0, obj=0.0, vtype=GRB.CONTINUOUS, name=variable_id)
        self.model.update()
        print("  ..constructing constraints to set ")
        for day in DAYS:
            for hour in pre_hours_real(day):
                for tutor in Data().tutor_by_name.keys():
                    for room in self.rooms:
                        expr = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour][room])])
                        expr2 = LinExpr([(1.0, self.schedule_entry_rooms[tutor][day][hour + 1][room])])
                        expr.add(expr2)
                        expr.addTerms(-1.0, self.same_room[day][hour][tutor][room])
                        constr_name = f"computeLocalDeviationFromTargetPlan1_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 1.0, name=constr_name)

                        expr = LinExpr([(-1.0, self.schedule_entry_rooms[tutor][day][hour][room])])
                        expr.addTerms(1.0, self.same_room[day][hour][tutor][room])
                        constr_name = f"computeLocalDeviationFromTargetPlan2_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 0.0, name=constr_name)

                        expr = LinExpr([(-1.0, self.schedule_entry_rooms[tutor][day][hour + 1][room])])
                        expr.addTerms(1.0, self.same_room[day][hour][tutor][room])
                        constr_name = f"computeLocalDeviationFromTargetPlan3_{day}_{hour}_{tutor}"
                        self.model.addConstr(expr, GRB.LESS_EQUAL, 0.0, name=constr_name)

        print(" ..final steps")
        expr = LinExpr([(1.0, self.same_room[day][hour][tutor][room])
                        for day in DAYS for hour in pre_hours_real(day)
                        for tutor in Data().tutor_by_name.keys() for room in self.rooms])
        self.model.setObjective(expr, GRB.MAXIMIZE)

        self.set_relative_mip_gap(0.01)
        self.set_time_limit(settings.optimization_parameters.time_limits.long._or(300)())
        self.model.setParam("NumericFocus", 2)
        self.model.setParam("MIPFocus", 1)

    def check_assignment(self, tutor, day, hour, task):
        if self.status is None or not self.status.is_feasible():
            print("ERROR!")
            return None
        return self.schedule_entry[tutor][day][hour][task].X > 0.5

    def find_room(self, tutor, day, hour):
        if self.status is None or not self.status.is_feasible():
            print("ERROR!")
            return None
        result = None
        for room in self.rooms:
            if self.schedule_entry_rooms[tutor][day][hour][room].X > 0.5:
                result = room
                break
        if result is None:
            print("ERROR!")
            return None
        return result

    def get_personal_plans(self):
        result = {}
        for tutor in Data().tutor_by_name.keys():
            new_plan = get_empty_plan()
            for day in DAYS:
                for hour in hours_real(day):
                    for task in TASKS:
                        new_plan[task][day][hour] = self.check_assignment(tutor, day, hour, task)
            result[tutor] = new_plan
        return result

    def get_personal_room_plans(self):
        result = {}
        for tutor in Data().tutor_by_name.keys():
            new_plan = get_empty_plan()
            for day in DAYS:
                for hour in hours_real(day):
                    for task in TASKS:
                        if self.check_assignment(tutor, day, hour, task):
                            new_plan[task][day][hour] = self.find_room(tutor, day, hour)
                        else:
                            new_plan[task][day][hour] = ""
            result[tutor] = new_plan
        return result

    def get_optimal_plan(self):
        new_plan = get_empty_plan()
        for day in DAYS:
            for hour in hours_real(day):
                for task in TASKS:
                    new_plan[task][day][hour] = sum([self.check_assignment(tutor, day, hour, task)
                                                     for tutor in Data().tutor_by_name.keys()])
        return new_plan

    def get_status(self):
        return self.status

    def write_solution(self, filename):
        self.model.write(filename + ".sol")

    def write_lp(self, filename):
        self.model.update()
        self.model.write(filename + "foo.lp")

    def set_relative_mip_gap(self, mip_gap):
        self.model.setParam('MIPGap', mip_gap)

    def set_time_limit(self, time_limit):
        self.model.setParam('TimeLimit', time_limit)

    def set_simplex_iterations(self, iterations):
        self.model.setParam('IterationLimit', iterations)
