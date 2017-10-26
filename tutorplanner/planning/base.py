"""
The ``base`` module contains functions that initial and rolling wave planning
have in common.
"""

__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "from_joint_plan_to_list",
    "evaluate_plan",
    "pickle_it",
    "compute_max_workload",
    "compute_min_happiness",
    "get_plan",
]

import pathlib
import pickle

from ..input import plan
from ..input.data import Data
from ..output import plot_happy_and_fair, day_index_to_string
from ..util import settings
from ..util.settings import DAYS, hours_real, TASKS, TUTORIUM


def from_joint_plan_to_list(tutor_plan, room_plan=None):
    """
    Create a list of TASKS for a tutor from a personal plan.
    """
    result = []
    for day in DAYS:
        changed = False
        for hour in hours_real(day):
            for task in TASKS:
                if tutor_plan[task][day][hour]:
                    if not changed:
                        result.append(day_index_to_string(day) + ":")
                        changed = True
                    if room_plan is not None:
                        result.append(f"{hour} Uhr bis {hour+1} Uhr --> {task} --> {room_plan[task][day][hour]}")
                    else:
                        result.append(f"{hour} Uhr bis {hour+1} Uhr --> {task}")

        if changed:
            result.append("\n")
    return result


def evaluate_plan(optimizer, folder: pathlib.Path, room_plan=None, print_to_screen=False, use_base_folder=False):
    """
    Write the plan as text for each tutor and add statistics like working
    hours, happiness. Plot the happiness and output some stuff. Also save the
    solver.
    """
    X = []
    Y = []
    tutor_plans = optimizer.get_personal_plans()
    if use_base_folder:
        optimizer_folder = folder
    else:
        optimizer_folder = folder / optimizer.name
    optimizer_folder.mkdir(parents=True, exist_ok=True)

    for tutor, tutor_plan in tutor_plans.items():

        contents =  "Tutor: " + tutor + "\t" + "\t \t".join([
            "Arbeitszeit (gesamt): " + str(plan.compute_workload(tutor_plan)),
            " Arbeitszeit (erste Woche): " + str(plan.compute_workload_first_week(tutor_plan)),
            " Arbeitszeit (zweite Woche): " + str(plan.compute_workload_second_week(tutor_plan)),
            "Happy?: Skala von 1 (nicht happy) bis 3 (sehr happy): "
            + str(plan.compute_happiness(tutor_plan, Data().availability[tutor]))
        ])
        contents += "\n\n"
        foo = None
        if room_plan is not None:
            foo = room_plan[tutor]
        contents += "\n".join(from_joint_plan_to_list(tutor_plan, foo))
        contents += "\n\n"

        with open(optimizer_folder / f"plan_{tutor}.txt", "w") as file:
            file.write(contents)

        if print_to_screen:
            print(contents)

        if Data().tutor_by_name[tutor].monthly_work_hours == 0:
            X.append(float("NaN"))
        else:
            X.append(plan.compute_workload(tutor_plan) / float(Data().tutor_by_name[tutor].monthly_work_hours / 2.0))
        Y.append(plan.compute_happiness(tutor_plan, Data().availability[tutor]))

    plot_happy_and_fair(X, Y, str(optimizer_folder))
    newPlan = optimizer.get_optimal_plan()
    #print "=== OLD ==="
    #pMP(plan, ordered=False)
    print("\n\n\n\n\n\n=== NEW ===")
    plan.print_master_plan(newPlan, ordered=False)
    print("\n\n\n\n\n\n")

    if room_plan is not None:
        print("Day\tcons\tcp2\tcp4\tcp6\tmax")
        for day in DAYS:
            sum_max_cap = sum([settings.get_room_info(room_plan[tutor][TUTORIUM][day][hour])["capacity"] for tutor in Data().tutor_by_name.keys() for hour in hours_real(day) if room_plan[tutor][TUTORIUM][day][hour] != ""])
            sum_conservative_sum = sum([min(settings.get_room_info(room_plan[tutor][TUTORIUM][day][hour])["capacity"], 35) for tutor in Data().tutor_by_name.keys() for hour in hours_real(day) if room_plan[tutor][TUTORIUM][day][hour] != ""])
            sum_conservative_p_2 = sum([min(settings.get_room_info(room_plan[tutor][TUTORIUM][day][hour])["capacity"], 35) + 2 for tutor in Data().tutor_by_name.keys() for hour in hours_real(day) if room_plan[tutor][TUTORIUM][day][hour] != ""])
            sum_conservative_p_4 = sum([min(settings.get_room_info(room_plan[tutor][TUTORIUM][day][hour])["capacity"], 35) + 4 for tutor in Data().tutor_by_name.keys() for hour in hours_real(day) if room_plan[tutor][TUTORIUM][day][hour] != ""])
            sum_conservative_p_6 = sum([min(settings.get_room_info(room_plan[tutor][TUTORIUM][day][hour])["capacity"], 35) + 6 for tutor in Data().tutor_by_name.keys() for hour in hours_real(day) if room_plan[tutor][TUTORIUM][day][hour] != ""])
            print("{}\t{}\t{}\t{}\t{}\t{}".format(day,sum_conservative_sum,sum_conservative_p_2,sum_conservative_p_4,sum_conservative_p_6,sum_max_cap))


    optimizer.write_lp(str(optimizer_folder))
    optimizer.write_solution(str(optimizer_folder))


def pickle_it(optimizer, folder: pathlib.Path, has_room_plans=False, use_base_folder=False):
    """
    Pack and save the generated plans.
    """
    if use_base_folder:
        optimizer_folder = folder
    else:
        optimizer_folder = folder / optimizer.name

    plan = optimizer.get_optimal_plan()
    with open(optimizer_folder / "plan.pickle", "wb") as file:
        pickle.dump(plan, file)

    tutor_plan = optimizer.get_personal_plans()
    with (optimizer_folder / "personalPlans.pickle").open("wb") as file:
        pickle.dump(tutor_plan, file)

    if has_room_plans:
        tutor_plan_rooms = optimizer.get_personal_room_plans()
        with open(optimizer_folder / "personalPlans_Rooms.pickle", "wb") as file:
            pickle.dump(tutor_plan_rooms, file)


def compute_max_workload(tutor_plans):
    """
    Compute the maximum workload of the tutors.
    """
    max_workload = 0.0
    for tutor in Data().tutor_by_name.keys():
        load = plan.compute_workload(tutor_plans[tutor]) / (Data().tutor_by_name[tutor].monthly_work_hours / 2.0)
        if load > max_workload:
            max_workload = load
    return max_workload


def compute_min_happiness(tutor_plans):
    """
    Compute the minimum happiness of the tutors.
    """
    min_happiness = 3.0
    for tutor in Data().tutor_by_name.keys():
        happiness = plan.compute_happiness(tutor_plans[tutor], Data().availability[tutor])
        if happiness < min_happiness:
            min_happiness = happiness
    return min_happiness


def get_plan(input_folder: pathlib.Path) -> plan.PersonalPlanDict:
    """
    Get the plan from the input folder.
    """
    with open(input_folder / "personalPlans_Rooms.pickle", "rb") as f:
        return pickle.load(f)
