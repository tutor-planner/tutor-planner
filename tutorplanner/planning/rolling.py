__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "main",
]

import pathlib

import click

from .base import evaluate_plan, pickle_it, compute_max_workload, compute_min_happiness, get_plan
from ..input import plan
from ..input.data import Data
from ..input.plan import get_target_plan
from ..gurobiinterface.rolling import PlanningCreator
from ..output import day_index_to_string
from ..util.settings import settings, TASKS, DAYS, hours_real


def write_diff(folder: pathlib.Path, old_plan, new_plan):
    for tutor_name in Data().tutor_by_name:
        tutor_diff = {}  # day index -> (old_task, new_task, old_room, new_room)
        for day in DAYS:
            for hour in hours_real(day):
                old_task = new_task = old_room = new_room = None
                for task in TASKS:
                    if old_plan[tutor_name][task][day][hour]:
                        old_task = task
                        old_room = old_plan[tutor_name][task][day][hour]
                    if new_plan[tutor_name][task][day][hour]:
                        new_task = task
                        new_room = new_plan[tutor_name][task][day][hour]
                if old_task != new_task or old_room != new_room:
                    tutor_diff.setdefault(day, {})[hour] = old_task, new_task, old_room, new_room
        output_lines = [f"Änderungen für {tutor_name}"]
        if not tutor_diff:
            output_lines.extend(["", "keine Änderungen"])
        for day in tutor_diff:
            output_lines.extend(["", day_index_to_string(day)])
            for hour in tutor_diff[day]:
                old_task, new_task, old_room, new_room = tutor_diff[day][hour]
                output_lines.append(f"{hour} Uhr bis {hour+1} Uhr")
                if old_task:
                    output_lines.append(f"  Aufgabe {old_task} in Raum {old_room} wurde entfernt.")
                if new_task:
                    output_lines.append(f"  Aufgabe {new_task} in Raum {new_room} wurde hinzugefügt.")
        (folder / f"changes_{tutor_name}.txt").write_text("\n".join(output_lines))


def main(next_day):
    """
    Run rolling wave planning.

    The rolling wave planning uses the active plan as input and tries to make
    few changes.
    """
    plan_paths = plan.get_plan_paths()
    input_folder = plan_paths["active"]
    if not input_folder or not input_folder.exists():
        click.secho(f"active plan not found: {input_folder}", fg="red", err=True)
        return
    click.secho(f"input plan: {plan_paths['active']}", fg="blue", bold=True)

    folder = plan.get_new_plan_folder("rolling")  # output folder

    target_plan = get_target_plan()
    past_plan = get_plan(input_folder)
    tutor_plans = None
    max_workload = None
    min_happiness = None

    level_solutions = {}

    for level in range(1, 10):
        # prepare
        if level == 1:
            pc = PlanningCreator(target_plan, past_plan=past_plan, next_day=next_day, level=level)
            pc.create_model_without_rooms()
            pc.plugin_constraint_bound_maximal_deviation_from_target_plan(max_deviation=0)
            pc.plugin_obj_minimize_deviation_from_plan()
            pc.fix_past_assignments()
        elif level == 2:
            pc = PlanningCreator(target_plan, past_plan=past_plan, next_day=next_day, level=level)
            pc.create_model_without_rooms()
            pc.plugin_constraint_bound_maximal_deviation_from_target_plan(max_deviation=0)
            pc.plugin_obj_maximize_task_contingency()
            pc.fix_past_assignments()
        elif level == 3:
            rel = settings.optimization_parameters.bounds.task_contingency._or(0.95)()
            pc.create_constraint_bound_task_contingency(pc.get_status().get_objective() * rel)
            pc.plugin_obj_minimize_work_spread()
        elif level == 4:
            rel = settings.optimization_parameters.bounds.maximal_work_spread._or(1.5)()
            pc.bound_maximal_work_spread(pc.get_status().get_objective() * rel)
            max_workload = compute_max_workload(tutor_plans)
            print(f"max_workload: {max_workload}")
            pc.plugin_obj_maximize_min_happiness(max_workload)
        elif level == 5:
            rel = settings.optimization_parameters.bounds.min_happiness._or(0.9)()
            min_happiness = compute_min_happiness(tutor_plans)
            print(f"min_happiness: {min_happiness}")
            pc.bound_min_happiness(max_workload, min_happiness * rel)
            pc.plugin_obj_maximize_cube_happiness()
        elif level == 6:
            rel = settings.optimization_parameters.bounds.cube_happiness._or(0.95)()
            for tutor in sorted(Data().tutor_by_name.keys()):
                happiness = plan.compute_happiness(tutor_plans[tutor], Data().availability[tutor])
                print(f"happiness of tutor {tutor} is {happiness}")

            cube_happiness = pc.get_status().get_objective()
            pc.bound_cube_happiness_from_below(cube_happiness * rel)

            pc.plugin_obj_minimize_mar_tel_hopping()
        elif level == 7:
            rel = settings.optimization_parameters.bounds.minimal_mar_tel_hopping._or(1.05)()
            pc.create_constraint_minimal_mar_tel_hopping(pc.get_status().get_objective() * rel)
            pc.extend_model_with_room_support()
            pc.fix_past_assignments_to_rooms()
            pc.plugin_objective_select_best_rooms()
        elif level == 8:
            rel = settings.optimization_parameters.bounds.best_rooms._or(0.999)()
            pc.bound_best_rooms_from_below(pc.get_status().get_objective() * rel)
            pc.plugin_obj_maximize_tutor_room_stability()
        elif level == 9:
            rel = settings.optimization_parameters.bounds.tutor_room_stability._or(0.9)()
            pc.bound_tutor_room_stability(pc.get_status().get_objective() * rel)
            pc.plugin_obj_maximize_task_room_contingency()

        pc.name = f"Level_{level}"

        # solve
        pc.solve_integer_program()

        if not pc.get_status().is_feasible():
            raise Exception(f"Aborted in phase {level}")

        level_solutions[level] = pc.get_status().get_objective()

        target_plan = pc.get_optimal_plan()
        tutor_plans = pc.get_personal_plans()
        if level < 7:
            evaluate_plan(pc, folder)
            pickle_it(pc, folder)
        else:
            personal_room_plans = pc.get_personal_room_plans()
            evaluate_plan(pc, folder, personal_room_plans)
            pickle_it(pc, folder, has_room_plans=True)

    # save last one again in base folder
    personal_room_plans = pc.get_personal_room_plans()
    evaluate_plan(pc, folder, personal_room_plans, use_base_folder=True)
    pickle_it(pc, folder, has_room_plans=True, use_base_folder=True)
    write_diff(folder, past_plan, personal_room_plans)

    print(f"THIS IS THE END \n\n\n{level_solutions}")

    # update active plan
    click.secho(f"old active plan: {plan_paths['active']}", fg="blue", bold=True)
    plan_paths["active"] = folder
    click.secho(f"new active plan: {plan_paths['active']}", fg="blue", bold=True)
    plan.save_plan_paths(plan_paths)

    # if you make mistakes, you can see where they are coming from
    plans_folder = pathlib.Path(settings.paths._get("plans", "plans")())
    (plan_paths["active"] / "parent_plan").write_text(f"{input_folder.relative_to(plans_folder)}\n")
