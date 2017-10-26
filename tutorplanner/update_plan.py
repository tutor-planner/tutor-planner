__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "from_personal_room_plan_to_plan",
    "from_personal_room_plan_to_personal_plan",
    "from_joint_plan_to_list",
    "evaluate_plan",
    "get_plan",
    "pickle_it",
    "search_room",
    "search_tutor",
    "search_date",
    "parse_date",
    "parse_task",
    "write_plans",
    "write_individual_changes",
]

import datetime
import pathlib
import pickle
import shutil
from typing import Tuple, Optional, List

import click

from .input import plan
from .input.data import Data
from .input.rooms import Room
from .input.tutor import Tutor
from .util import converter
from .util.settings import settings, DAYS, hours_real, TASKS


LOG_FILE = "changes.log"


def from_personal_room_plan_to_plan(personal_room_plan):
    """
    Convert personal room plan dict to plan dict.
    """
    def check_assignment(tutor, day, hour, task):
        return personal_room_plan[tutor][task][day][hour] != ""

    output_plan = plan.get_empty_plan()
    for day in DAYS:
            for hour in hours_real(day):
                for task in TASKS:
                    output_plan[task][day][hour] = sum([check_assignment(tutor, day, hour, task) for tutor in Data().tutor_by_name.keys()])
    return output_plan


def from_personal_room_plan_to_personal_plan(personal_room_plan):
    """
    Convert personal room plan dict to personal plan dict.
    """
    def check_assignment(tutor, day, hour, task):
        return personal_room_plan[tutor][task][day][hour] != ""

    result = {}
    for tutor in Data().tutor_by_name.keys():
        new_plan = plan.get_empty_plan()
        for day in DAYS:
            for hour in hours_real(day):
                for task in TASKS:
                    new_plan[task][day][hour] = check_assignment(tutor, day, hour, task)
        result[tutor] = new_plan
    return result


def from_joint_plan_to_list(tutor_plan, tutor_room_plan=None) -> List[str]:
    """
    Generate tutor plan as text.
    """
    result = []
    for day in DAYS:
        changed = False
        for hour in hours_real(day):
            for task in TASKS:
                if tutor_plan[task][day][hour]:
                    if not changed:
                        result.append(f"Tag {day}:")
                        changed = True
                    if tutor_room_plan is not None:
                        result.append(f"{hour} Uhr bis {hour+1} Uhr --> {task} --> {tutor_room_plan[task][day][hour]}")
                    else:
                        result.append(f"{hour} Uhr bis {hour+1} Uhr --> {task}")

        if changed:
            result.append("\n")
    return result


def evaluate_plan(folder: pathlib.Path, updated_plan, personal_plans, room_plan=None, print_to_screen: bool = False) -> None:
    """
    Write individual plans as text files.
    """
    for tutor, tutor_plan in personal_plans.items():
        contents = (
            f"Tutor:"
            f" {tutor}\t"
            f"Arbeitszeit (gesamt):"
            f" {plan.compute_workload(tutor_plan)}\t\t"
            f"Arbeitszeit (erste Woche):"
            f" {plan.compute_workload_first_week(tutor_plan)}\t\t"
            f"Arbeitszeit (zweite Woche):"
            f" {plan.compute_workload_second_week(tutor_plan)}\t\t"
            f"Happy?: Skala von 1 (nicht happy) bis 3 (sehr happy):"
            f" {plan.compute_happiness(tutor_plan, Data().availability[tutor])}"
        )
        contents += "\n\n"
        tutor_room_plan = (room_plan or {})[tutor]
        contents += "\n".join(from_joint_plan_to_list(tutor_plan, tutor_room_plan))
        contents += "\n\n"

        (folder / f"plan_{tutor}.txt").write_text(contents)

        if print_to_screen:
            print(contents)

    plan.print_master_plan(updated_plan, ordered=False)


def get_plan(folder: pathlib.Path) -> plan.PersonalPlan:
    """
    Get the plan from folder.
    """
    with open(folder / "personalPlans_Rooms.pickle", "rb") as f:
        plan_dict = pickle.load(f)
    return plan.PersonalPlan.create_from_personal_plan(plan_dict)


def pickle_it(folder: pathlib.Path, plan, personal_plans, personal_room_plans):
    """
    Pickle and save all plan dicts.
    """
    with open(folder / "plan.pickle", "wb") as file:
        pickle.dump(plan, file)
    with open(folder / "personalPlans.pickle", "wb") as file:
        pickle.dump(personal_plans, file)
    with open(folder / "personalPlans_Rooms.pickle", "wb") as file:
        pickle.dump(personal_room_plans, file)


def search_room(room_name: str) -> Room:
    """
    Search room by lowercase name.
    """
    all_rooms = Data().room_by_name.values()
    for room in all_rooms:
        if room.name.lower() == room_name.lower():
            return room
    raise ValueError(f"room not found: {room_name}")


def search_tutor(tutor_name: str) -> Tutor:
    """
    Search tutor by lowercase name.
    """
    tutors = Data().tutor_by_name.values()
    for t in tutors:
        if t.last_name.lower() == tutor_name.lower():
            return t
    raise ValueError(f"tutor not found: {tutor_name}")


def search_date(month: int, day: int) -> Optional[datetime.date]:
    """
    Search date in settings.
    """
    for date in settings.days():
        if date.month == month and date.day == day:
            return date
    return None


def parse_date(date_str: str) -> datetime.date:
    """
    Parse date and time of the format [YYYY-]MM-DD HH.

    Returns a tuple of date and hour.
    """
    try:
        date_parts = list(map(int, date_str.split("-")))
    except ValueError:
        raise ValueError(f"invalid date format: {date_str}")
    if len(date_parts) > 3 or len(date_parts) < 2:
        raise ValueError(f"invalid date format: {date_str}")
    if len(date_parts) == 2:
        date = search_date(*date_parts)
        if date is None:
            raise ValueError(f"date not in settings: {date_str}")
    else:
        date = datetime.date(*date_parts)
        if date not in settings.days():
            raise ValueError(f"date not in settings: {date_str}")
    return date


def parse_task(task: str, room_required: bool = True) -> Tuple[Tutor, datetime.date, int, Optional[Room]]:
    """
    Parse a task.

    If the room is not required, ``None`` is returned instead of the room.
    """
    task_parts = task.strip().split()
    if room_required and len(task_parts) == 4 or not room_required and 3 <= len(task_parts) <= 4:
        tutor = search_tutor(task_parts.pop(0).replace("_", " "))
        day = parse_date(task_parts.pop(0))
        hour = int(task_parts.pop(0))

        if task_parts:
            room = search_room(task_parts.pop(0).replace("_", " "))
        else:
            room = None

        return tutor, day, hour, room
    else:
        raise ValueError("expected TUTOR DATE HOUR ROOM")


def write_plans(folder: pathlib.Path, personal_plan: plan.PersonalPlan) -> None:
    """
    Write all plans into working.
    """
    updated_personal_room_plan = personal_plan.get_personal_plan()
    updated_plan = from_personal_room_plan_to_plan(updated_personal_room_plan)
    updated_personal_plan = from_personal_room_plan_to_personal_plan(updated_personal_room_plan)
    pickle_it(folder, updated_plan, updated_personal_plan, updated_personal_room_plan)
    evaluate_plan(folder, updated_plan, updated_personal_plan, updated_personal_room_plan)


def write_individual_changes(working_path: pathlib.Path) -> None:
    """
    Use log to write individual changes.
    """
    changes_by_tutor = {tutor_name: [] for tutor_name in Data().tutor_by_name}

    with open(working_path / LOG_FILE) as f:
        for line in f:
            line = line.rstrip()
            action, *tasks_str = line.split(";")
            tasks = list(map(parse_task, tasks_str))
            if action == "add" or action == "remove":
                changes_by_tutor[tasks[0][0].last_name].append((action, tasks[0]))
            else:
                # action == "switch"
                changes_by_tutor[tasks[0][0].last_name].append(("remove", tasks[0]))
                changes_by_tutor[tasks[1][0].last_name].append(("add", tasks[1]))

    action_map = dict(add="hinzugefügt", remove="entfernt")
    for tutor_name, tutor_changes in changes_by_tutor.items():
        with open(working_path / f"changes_{tutor_name}.txt", "w") as f:
            print(f"Änderungen für {tutor_name}", file=f)
            if not tutor_changes:
                print("\nkeine Änderungen", file=f)
                continue
            last_date = None
            for action, (tutor, date, hour, room) in sorted(tutor_changes, key=lambda x: x[1][:2]):
                if date != last_date:
                    print(f"\nTag {converter.date_to_day_index(date)} ({date})", file=f)
                    last_date = date
                print(f"{hour} Uhr bis {hour + 1} Uhr --> {plan.type_map[room.type]} --> {room}   {action_map[action]}",
                      file=f)


@click.group()
def cli_state():
    """
    Show or change the active and working plans.
    """


@cli_state.command("init-working")
@click.option("--description")
def initialize_working_plan(description):
    """
    Copy the active plan to a working copy.
    """
    if description is None:
        description = ""
    else:
        description = "-" + description

    # copy all pickle files to a new folder
    plan_paths = plan.get_plan_paths()
    active = plan_paths["active"]

    if not active or not active.is_dir():
        click.secho("active plan does not exist", fg="red", err=True)
        return

    new_folder = plan.get_new_plan_folder("manual-updates" + description)

    new_folder.mkdir()
    for filename in ("plan.pickle", "personalPlans.pickle", "personalPlans_Rooms.pickle"):
        shutil.copyfile(str(active / filename), str(new_folder / filename))

    # if you make mistakes, you can see where they are coming from
    plans_folder = pathlib.Path(settings.settings.paths._get("plans", "plans")())
    (new_folder / "parent_plan").write_text(f"{active.relative_to(plans_folder)}\n")

    (new_folder / LOG_FILE).touch()

    # set the path of the working folder
    click.secho(f"old working plan: {plan_paths['working']}")
    plan_paths["working"] = new_folder
    click.secho(f"new working plan: {plan_paths['working']}")
    click.secho(f"copied from active: {plan_paths['active']}")
    plan.save_plan_paths(plan_paths)


@cli_state.command("activate-working")
def activate_working_plan():
    """
    Set the active plan to the working plan and unset the working plan.
    """
    plan_paths = plan.get_plan_paths()
    if not plan_paths["working"] or not plan_paths["working"].is_dir():
        click.secho("working plan does not exist", fg="red", err=True)
        return
    click.secho(f"old active plan: {plan_paths['active']}")
    plan_paths["active"] = plan_paths["working"]
    click.secho(f"new active plan: {plan_paths['active']}")
    plan_paths["working"] = None
    plan.save_plan_paths(plan_paths)


@cli_state.command("activate-parent")
def activate_parent():
    """
    Activate predecessor of currently active plan if it exists.

    A plan has a parent plan if it is generated by rolling-wave planning or
    init-working.
    """
    plan_paths = plan.get_plan_paths()
    if not plan_paths["parent"] or not plan_paths["parent"].is_dir():
        click.secho("parent plan does not exist", fg="red", err=True)
        return
    click.secho(f"old active plan: {plan_paths['active']}")
    plan_paths["active"] = plan_paths["parent"]
    click.secho(f"new active plan: {plan_paths['active']}")
    plan.save_plan_paths(plan_paths)


@cli_state.command("show")
def status():
    """
    Show the status of the working plan.

    The status information contains the paths of the active and the working
    plan and some statistics.
    """
    plan_paths = plan.get_plan_paths()
    parent = plan_paths["parent"]
    active = plan_paths["active"]
    working = plan_paths["working"]
    if parent:
        print("parent of active:", parent)
    print("active:", active)
    print("working:", working)

    if working:
        print()
        try:
            with open(working / LOG_FILE) as f:
                log_lines = f.readlines()
                print(len(log_lines), "changes")
                if log_lines:
                    print("last change:", log_lines[-1].rstrip())
        except IOError as e:
            print(e)


@click.group()
def cli_update():
    """
    Update the plan manually.
    """


@cli_update.command("switch")
@click.argument("old_task")
@click.argument("new_task")
def switch_task(old_task, new_task):
    """
    Switch the task to a new task.
    """
    plan_paths = plan.get_plan_paths()
    if not plan_paths["working"] or not plan_paths["working"].is_dir():
        click.secho("working plan does not exist", fg="red", err=True)
        return

    working_plan = get_plan(plan_paths["working"])

    try:
        old_tutor, old_day, old_hour, old_room = parse_task(old_task, room_required=False)
    except ValueError as e:
        print(e)
        return
    try:
        new_tutor, new_day, new_hour, new_room = parse_task(new_task)
    except ValueError as e:
        print(e)
        return

    try:
        old_room = working_plan.remove_task(old_tutor, old_day, old_hour, old_room)
        working_plan.add_task(new_tutor, new_day, new_hour, new_room)
    except ValueError as e:
        print(e)
    else:
        write_plans(plan_paths["working"], working_plan)
        print("old task:", old_tutor, old_day, old_hour, old_room, old_room.type)
        print("new task:", new_tutor, new_day, new_hour, new_room, new_room.type)
        with open(plan_paths["working"] / LOG_FILE, "a") as file:
            print("switch;{} {} {} {};{} {} {} {}".format(
                old_tutor.last_name.replace(" ", "_"),
                old_day,
                old_hour,
                old_room.name.replace(" ", "_"),
                new_tutor.last_name.replace(" ", "_"),
                new_day,
                new_hour,
                new_room.name.replace(" ", "_"),
            ), file=file)
        write_individual_changes(plan_paths["working"])


@cli_update.command("add")
@click.argument("new_task")
def add_task(new_task):
    """
    Add a task.

    new_task consists of:
    - tutor name
    - date and hour
    - room name

    The date format is YYYY-MM-DD or MM-DD.

    Please note that you have to write an underscore for every space in tutor
    and room names.
    """
    plan_paths = plan.get_plan_paths()
    if not plan_paths["working"] or not plan_paths["working"].is_dir():
        click.secho("working plan does not exist", fg="red", err=True)
        return

    working_plan = get_plan(plan_paths["working"])

    try:
        tutor, day, hour, room = parse_task(new_task)
        working_plan.add_task(tutor, day, hour, room)
    except ValueError as e:
        print(e)
    else:
        write_plans(plan_paths["working"], working_plan)
        print("new task:", tutor, day, hour, room, room.type)
        with open(plan_paths["working"] / LOG_FILE, "a") as file:
            print("add;{} {} {} {}".format(
                tutor.last_name.replace(" ", "_"),
                day,
                hour,
                room.name.replace(" ", "_"),
            ), file=file)
        write_individual_changes(plan_paths["working"])


@cli_update.command("remove")
@click.argument("old_task")
def remove_task(old_task):
    """
    Remove a task.

    old_task consists of:
    - tutor name
    - date and hour
    - room name (optional)

    The date format is YYYY-MM-DD or MM-DD.

    Please note that you have to write an underscore for every space in tutor
    and room names.
    """
    plan_paths = plan.get_plan_paths()
    if not plan_paths["working"] or not plan_paths["working"].is_dir():
        click.secho("working plan does not exist", fg="red", err=True)
        return

    working_plan = get_plan(plan_paths["working"])

    try:
        tutor, day, hour, room = parse_task(old_task, room_required=False)
        room = working_plan.remove_task(tutor, day, hour, room)
    except ValueError as e:
        print(e)
    else:
        write_plans(plan_paths["working"], working_plan)
        print("old task:", tutor, day, hour, room, room.type)
        with open(plan_paths["working"] / LOG_FILE, "a") as file:
            print("remove;{} {} {} {}".format(
                tutor.last_name.replace(" ", "_"),
                day,
                hour,
                room.name.replace(" ", "_"),
            ), file=file)
        write_individual_changes(plan_paths["working"])


@cli_update.command("undo")
def undo_last_change():
    """
    Undo last change.
    """
    plan_paths = plan.get_plan_paths()
    if not plan_paths["working"] or not plan_paths["working"].is_dir():
        click.secho("working plan does not exist", fg="red", err=True)
        return

    working_plan = get_plan(plan_paths["working"])

    with open(plan_paths["working"] / LOG_FILE) as f:
        log_lines = f.readlines()
    if not log_lines:
        click.secho("log is empty", fg="red", err=True)
        return

    last_line = log_lines[-1].rstrip()
    action, *tasks = last_line.split(";")

    try:
        task1 = parse_task(tasks[0], room_required=(action == "add"))
    except ValueError as e:
        print(e)
        return

    try:
        if action == "add" and len(tasks) == 1:
            working_plan.remove_task(*task1)
        elif action == "remove" and len(tasks) == 1:
            working_plan.add_task(*task1)
        elif action == "switch" and len(tasks) == 2:
            try:
                task2 = parse_task(tasks[1])
            except ValueError as e:
                print(e)
                return
            working_plan.remove_task(*task2)
            working_plan.add_task(*task1)
        else:
            click.secho("cannot parse log line", fg="red", err=True)
            return
    except ValueError as e:
        print(e)
    else:
        write_plans(plan_paths["working"], working_plan)
        print("undid", last_line)
        with open(plan_paths["working"] / LOG_FILE, "w") as f:
            f.writelines(log_lines[:-1])
        write_individual_changes(plan_paths["working"])
