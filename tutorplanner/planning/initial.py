__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "main",
]

import click

from .base import evaluate_plan, pickle_it, compute_max_workload, compute_min_happiness
from ..input import plan
from ..input.data import Data
from ..input.plan import get_target_plan
from ..gurobiinterface.initial import PlanningCreator
from ..util.settings import settings


def main():
    """
    Run initial planning.
    """
    folder = plan.get_new_plan_folder("initial")

    target_plan = get_target_plan()
    tutor_plans = None
    max_workload = None
    min_happiness = None

    level_solutions = {}

    for level in range(1, 8):
        # prepare
        if level == 1:
            pc = PlanningCreator(target_plan, level=level)
            pc.create_model_without_rooms()
            pc.plugin_constraint_bound_maximal_deviation_from_target_plan(max_deviation=0)
            pc.plugin_obj_minimize_deviation_from_plan()
        elif level == 2:
            pc = PlanningCreator(target_plan, level=level)
            pc.create_model_without_rooms()
            pc.plugin_constraint_bound_maximal_deviation_from_target_plan(max_deviation=0)
            pc.plugin_obj_minimize_work_spread()
        elif level == 3:
            rel = settings.optimization_parameters.bounds.maximal_work_spread._or(1.5)()
            pc.bound_maximal_work_spread(pc.get_status().get_objective() * rel)
            max_workload = compute_max_workload(tutor_plans)
            print(f"max_workload: {max_workload}")
            pc.plugin_obj_maximize_min_happiness(max_workload)
        elif level == 4:
            rel = settings.optimization_parameters.bounds.min_happiness._or(0.9)()
            min_happiness = compute_min_happiness(tutor_plans)
            print(f"min_happiness: {min_happiness}")
            pc.bound_min_happiness(max_workload, min_happiness * rel)
            pc.plugin_obj_maximize_cube_happiness()
        elif level == 5:
            rel = settings.optimization_parameters.bounds.cube_happiness._or(0.95)()
            for tutor in sorted(Data().tutor_by_name.keys()):
                happiness = plan.compute_happiness(tutor_plans[tutor], Data().availability[tutor])
                print(f"happiness of tutor {tutor} is {happiness}")

            cube_happiness = pc.get_status().get_objective()
            pc.bound_cube_happiness_from_below(cube_happiness * rel)

            pc.plugin_obj_minimize_mar_tel_hopping()
        elif level == 6:
            rel = settings.optimization_parameters.bounds.minimal_mar_tel_hopping._or(1.05)()
            pc.create_constraint_minimal_mar_tel_hopping(pc.get_status().get_objective() * rel)
            pc.extend_model_with_room_support()
            pc.plugin_objective_select_best_rooms()
        elif level == 7:
            rel = settings.optimization_parameters.bounds.best_rooms._or(0.999)()
            pc.bound_best_rooms_from_below(pc.get_status().get_objective() * rel)
            pc.plugin_obj_maximize_tutor_room_stability()

        pc.name = f"Level_{level}"

        # solve
        pc.solve_integer_program()

        if not pc.get_status().is_feasible():
            raise Exception(f"Aborted in phase {level}")

        level_solutions[level] = pc.get_status().get_objective()

        target_plan = pc.get_optimal_plan()
        tutor_plans = pc.get_personal_plans()
        if level < 6:
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

    print(f"THIS IS THE END \n\n\n{level_solutions}")

    # update active plan
    plan_paths = plan.get_plan_paths()
    click.secho(f"old active plan: {plan_paths['active']}", fg="blue", bold=True)
    plan_paths["active"] = folder
    click.secho(f"new active plan: {plan_paths['active']}", fg="blue", bold=True)
    plan.save_plan_paths(plan_paths)
