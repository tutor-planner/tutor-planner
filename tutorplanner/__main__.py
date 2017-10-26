__author__ = ("Alexander Elvers <aelvers AT inet.tu-berlin.de>, "
              "Matthias Rost <mrost AT inet.tu-berlin.de>")

import glob
import itertools
import re

import click
from pathlib import Path

from . import read_pickled_files as rpf, output, update_plan
from .input import lsf_parser, rooms, plan
from .input.data import Data
from .planning import initial, rolling, base as base_planning
from .util import settings, converter
from .util.settings import DAYS, hours_real, TUTORIUM


@click.group()
def cli():
    pass


cli.add_command(output.cli, "output")
cli.add_command(update_plan.cli_state, "state")
cli.add_command(update_plan.cli_update, "update-plan")


@cli.group()
def planning():
    """
    Run planner.
    """


@planning.command("initial")
def planning_initial():
    """
    Run initial planner.

    Initial planning starts from scratch.
    """
    initial.main()


@planning.command("rolling")
@click.argument("next_day")
def planning_rolling(next_day):
    """
    Run rolling wave planner.

    Rolling wave planning is based on an existing plan and creates a new plan.
    It tries to minimize the changes of the plan.

    For days before next_day, the active plan is used. The first day that can
    have changes in rolling wave planning is next_day.
    """
    days = settings.settings.days._or([])()
    days_dict = dict([(f"{d:%m-%d}", d) for d in days] + [(f"{d:%Y-%m-%d}", d) for d in days])
    if next_day not in days_dict:
        raise click.BadParameter(f"invalid choice {next_day}. (choose from {', '.join(days_dict.keys())})")
    next_day = days_dict[next_day]
    next_day_index = converter.date_to_day_index(next_day)

    rolling.main(next_day_index)


@cli.command("lsf-to-csv")
@click.argument("lsf_files")
@click.argument("csv_file")
def lsf_to_csv(lsf_files, csv_file):
    """
    Convert all LSF files to CSV. The lsf_files are a glob pattern, e.g.
    'data/*.xml', so it's better to quote. The csv_file is the output file.
    """
    for file in glob.glob(lsf_files):
        print("read", file)

    booked_rooms = lsf_parser.parse_files(glob.glob(lsf_files))
    booked_rooms_dict = {room.name: room for room in booked_rooms}

    print("write", csv_file)
    rooms.export_rooms_to_csv(csv_file, booked_rooms)


@cli.command("lsf-to-xlsx")
@click.argument("output_file")
@click.option("--lsf-xml-input-files", default=None, help="booking files in xml from lsf (glob pattern)")
@click.option("--csv-input-files", default=None, help="booking files in csv (glob pattern)")
@click.option("--type", default=None, help="one of the potential room types")
@click.option("--include", default=None, help="a regular expression that room names have to match")
@click.option("--exclude", default=None, help="a regular expression that room names have to NOT match")
@click.option("--export-capacity", is_flag=True, help="if enabled, the export writes the room capacity instead of a flag")
@click.option("--maximal-tutorial-size", default=5000, help="maximal size of tutorials (default is a large number)")
@click.option("--verbose", "-v", is_flag=True, help="show more information")
def lsf_to_xlsx(output_file, lsf_xml_input_files, csv_input_files, type, include, exclude, export_capacity, maximal_tutorial_size, verbose):
    """
    Convert room booking files from LSF or CSV to xlsx. Filters the rooms by
    room type or room name.

    If include is given, all rooms are exported that match the expression.
    If exclude is given, rooms matching the expression are excluded.

    It's better to quote regular expressions or glob patterns.
    """
    if verbose:
        print(f"selected include filter: {include}")
        print(f"selected exclude filter: {exclude}")
        print(f"selected type:           {type}")
        print(f"export_capacity:         {export_capacity}")
        print(f"output_file:             {output_file}")
        print(f"lsf_xml_input_files:     {lsf_xml_input_files}")
        print(f"csv_input_files:         {csv_input_files}")

    booked_rooms = []

    if lsf_xml_input_files is not None:
        for file in glob.glob(lsf_xml_input_files):
            if verbose:
                print("read", file)
            booked_rooms = lsf_parser.parse_files([file], initial_rooms=booked_rooms)

    if csv_input_files is not None:
        for file in glob.glob(csv_input_files):
            if verbose:
                print("read", file)
            booked_rooms = rooms.import_rooms_from_csv(file, initial_rooms=booked_rooms)

    filtered_rooms = []

    regex_include = None
    regex_exclude = None
    if include is not None:
        regex_include = re.compile(include, re.IGNORECASE)

    if exclude is not None:
        regex_exclude = re.compile(exclude, re.IGNORECASE)

    for room in booked_rooms:
        if type is not None and room.type != type:
            if verbose:
                print(f"room type {room.type} did not match {type}")
            continue
        if regex_include is not None and not regex_include.match(room.name):
            if verbose:
                print(f"room {room.name} was discarded due to include filter ")
            continue
        if regex_exclude is not None and regex_exclude.match(room.name):
            if verbose:
                print(f"room {room.name} was discarded due to exclude filter")
            continue
        filtered_rooms.append(room)

    if verbose:
        print(filtered_rooms)

        print("write", output_file)
    rooms.export_rooms_to_xlsx(output_file, filtered_rooms, export_capacity=export_capacity, maximal_tutorial_size=maximal_tutorial_size)


@cli.command("room-info")
@click.argument("csv_file")
@click.option("--room", "room_name", default="", help="room name should start with this")
@click.option("--type", default=None, help="room type")
@click.option("--projector/--no-projector", default=None, help="room has projector/no projector")
def room_info(csv_file, room_name, type, projector):
    """
    Print room information, i.e. room name, room type, capacity, projector.
    The room names are read from csv and the rest from settings.
    """
    booked_rooms = rooms.import_rooms_from_csv(csv_file)
    room_count = 0
    capacity_sum = 0
    for room in sorted(booked_rooms, key=lambda x: x.name):
        info = settings.get_room_info(room.name)
        if (
            room.name.startswith(room_name) and
            (type is None or info["type"] == type) and
            (projector is None or info["projector"] == projector)
        ):
            if info["type"] is None:
                print(f"WARNING: cannot find type of {room.name}")
            if info["capacity"] is None:
                print(f"WARNING: cannot find capacity of {room.name}")
            if info["projector"] is None:
                print(f"WARNING: cannot find projector of {room.name}")
            print("Name:", room.name)
            print("Type:", info["type"])
            print("Capacity:", info["capacity"])
            print("Projector:", info["projector"])
            print(30 * "-")
            room_count += 1
            if info["capacity"] is not None:
                capacity_sum += info["capacity"]
    print(room_count, "rooms")
    print("capacity:", capacity_sum)


@cli.command("check-tutor-responses")
def check_tutor_responses():
    """
    Check tutor responses.
    """
    tutors = Data().tutor_by_name.values()
    print("Tutors without problems:")
    for t in tutors:
        print(t)


@cli.command("export-plan")
@click.option("--output", default=None, help="output file")
@click.option("--empty", is_flag=True, help="write empty plan")
@click.option("--pickled", is_flag=True, help="write pickled plan")
@click.option("--diff", is_flag=True, help="write difference of plans")
def export_plan(output, empty, pickled, diff):
    """
    Export plan to xlsx.
    """
    if not (empty or pickled or diff):
        print("nothing to do")
        return
    with plan.export_plan_to_xlsx(output) as wb:
        if empty:
            print("write empty plan")
            empty_plan = plan.get_empty_plan()
            try:
                del wb["Target"]
            except KeyError:
                pass
            ws = wb.create_sheet("Target", 0)
            plan.write_plan_to_worksheet(ws, empty_plan)
        if pickled:
            print("write output plan")
            pickled_plan = update_plan.from_personal_room_plan_to_plan(rpf.get_active_plan_dict())
            try:
                del wb["Output"]
            except KeyError:
                pass
            ws = wb.create_sheet("Output", 1)
            plan.write_plan_to_worksheet(ws, pickled_plan)
        # if diff:
        #     print("write diff")
        #     try:
        #         del wb["Diff"]
        #     except KeyError:
        #         pass
        #     ws = wb.create_sheet("Diff", 2)
        #     plan.write_plan_to_worksheet(ws, None)


@cli.command("check-plan")
@click.option("--lsf-xml-input-files", default=None, help="booking files in xml from lsf (glob pattern)")
@click.option("--csv-input-files", default=None, help="booking files in csv (glob pattern)")
def check_plan(lsf_xml_input_files, csv_input_files):
    booked_rooms = []

    if lsf_xml_input_files is not None:
        for file in glob.glob(lsf_xml_input_files):
            booked_rooms = lsf_parser.parse_files([file], initial_rooms=booked_rooms)

    if csv_input_files is not None:
        for file in glob.glob(csv_input_files):
            booked_rooms = rooms.import_rooms_from_csv(file, initial_rooms=booked_rooms)

    pickled_plan = rpf.get_active_plan_dict()

    errors = plan.check_plan(pickled_plan, booked_rooms)

    print("\033[1;29mPlan: ", end="")
    if not errors:
        print("\033[32mok\033[0m")
    else:
        print("\033[31merrors\033[0m")
        for error in errors:
            print(*error)


@cli.command("tutorial-seat-overview")
def tutorial_seat_overview():
    room_plan = rpf.get_active_plan_dict()

    tutorial_caps = [24, 27, 30, 33]
    overprovisioning = [0, 1, 2, 3, 4]

    combos = [(tc, op) for op, tc in itertools.product(overprovisioning, tutorial_caps)]

    string_combos = [f"{tc},{op}" for tc, op in combos]
    header = "Day\t" + "\t".join(string_combos)
    print(header)
    for day in DAYS:
        value_list = []
        for tc, op in combos:
            value_list.append(sum([(min(settings.get_room_info(room_plan[tutor][TUTORIUM][day][hour])["capacity"],tc) + op) for tutor in Data().tutor_by_name.keys() for hour in hours_real(day) if room_plan[tutor][TUTORIUM][day][hour] != ""]))
        print("\t".join([str(day)] + [str(v) for v in value_list]))


@cli.command("find-available-tutors")
@click.argument("day")
@click.argument("hour", type=int)
def find_available_tutors(day, hour):
    """
    Find available tutor at given time.
    """
    original_day = day
    days = settings.settings.days._or([])()
    days_dict = dict([(f"{d:%m-%d}", d) for d in days] + [(f"{d:%Y-%m-%d}", d) for d in days])
    if day not in days_dict:
        raise click.BadParameter(f"invalid choice {day}. (choose from {', '.join(days_dict.keys())})")
    day = days_dict[day]
    day_index = converter.date_to_day_index(day)

    plan_paths = plan.get_plan_paths()
    plan_folder = plan_paths["active"]
    if not plan_folder or not plan_folder.exists():
        click.secho(f"active plan not found: {plan_folder}", fg="red", err=True)
        return

    active_plan = base_planning.get_plan(plan_folder)

    tutors_by_availability = {i: [] for i in range(4)}
    tutor_has_a_task = set()
    for tutor_name, tutor_availability in Data().availability.items():
        tutors_by_availability[tutor_availability[day_index][hour]].append(tutor_name)
        for task in settings.TASKS:
            if active_plan[tutor_name][task][day_index][hour]:
                tutor_has_a_task.add(tutor_name)
                break

    tutors_by_name = Data().tutor_by_name

    print(f"\nTutor availability on {original_day} at {hour} o'clock. \n\n")
    for i in [3, 2, 1, 0]:
        click.secho(f"availability {i}", fg="blue")
        tutors = tutors_by_availability[i]
        for tutor_name in tutors:
            if tutor_name in tutor_has_a_task:
                has_task_str = " (has already a task)"
            else:
                has_task_str = ""
            click.secho(f"- {tutor_name}{has_task_str} [ {tutors_by_name[tutor_name].email} ]", fg=(not has_task_str) * "yellow")
        click.echo()


@cli.command("tutor-mail-addresses")
def tutor_mail_addresses():
    """
    Just print mail-addresses ordered according to last name
    """
    tutors_by_name = Data().tutor_by_name
    for tutor_name in sorted(tutors_by_name.keys()):
        print(f"{tutor_name:20s} {tutors_by_name[tutor_name].first_name:20s}: {tutors_by_name[tutor_name].email:30s}")


@cli.command("show-working-tutors")
@click.argument("day")
@click.argument("hour", type=int)
def show_working_tutors(day, hour):
    original_day = day
    days = settings.settings.days._or([])()
    days_dict = dict([(f"{d:%m-%d}", d) for d in days] + [(f"{d:%Y-%m-%d}", d) for d in days])
    if day not in days_dict:
        raise click.BadParameter(f"invalid choice {day}. (choose from {', '.join(days_dict.keys())})")
    day = days_dict[day]
    day_index = converter.date_to_day_index(day)


    pickled_plan = rpf.get_active_plan_dict()
    #print(pickled_plan)

    working_tutors = {i: [] for i in range(1,4)}
    tutor_has_a_task = set()
    for tutor_name, tutor_availability in Data().availability.items():
        task_of_tutor = None

        availability = tutor_availability[day_index][hour]
        workload_of_tutor = _relative_workload_of_tutor(tutor_name, pickled_plan[tutor_name])

        for task in settings.TASKS:
            if pickled_plan[tutor_name][task][day_index][hour]:
                task_of_tutor = [tutor_name, availability, workload_of_tutor, task, pickled_plan[tutor_name][task][day_index][hour]]
                tutor_has_a_task.add(tutor_name)
                working_tutors[availability].append(task_of_tutor)
                break

    tutors_by_name = Data().tutor_by_name

    print(f"\nWorking tutors on {original_day} at {hour} o'clock. \n\n")
    for i in [3, 2, 1]:
        click.secho(f"tutors with availability {i}", fg="blue")
        tutors = working_tutors[i]
        for element in tutors:
            #print(working_tutors[i])
            tutor_name, availability, workload, task, room = element
            click.secho(
                f"- {tutor_name:16s}: {task:20s} in {room:10s}; \tavailability: {availability};\t workload: {workload:.2f} \t\t[{tutors_by_name[tutor_name].email:25s} ]",
                fg="yellow")
        click.echo()


def _relative_workload_of_tutor(tutor_name, tutor_plan):
    return plan.compute_workload(tutor_plan) / float(Data().tutor_by_name[tutor_name].monthly_work_hours / 2.0)


@cli.command("output-diff-of-plans")
@click.argument("path_to_old_plan")
@click.argument("path_to_new_plan")
@click.argument("output_folder")
def output_diff_of_plans(path_to_old_plan, path_to_new_plan, output_folder):
    path_to_old_plan = Path(path_to_old_plan)
    path_to_new_plan = Path(path_to_new_plan)
    output_folder = Path(output_folder)

    old_plan = base_planning.get_plan(path_to_old_plan)
    new_plan = base_planning.get_plan(path_to_new_plan)

    rolling.write_diff(output_folder, old_plan, new_plan)

    X = []
    Y = []

    for tutor, tutor_plan in new_plan.items():
        if Data().tutor_by_name[tutor].monthly_work_hours == 0:
            X.append(float("NaN"))
        else:
            X.append(_relative_workload_of_tutor(tutor, tutor_plan))
        Y.append(plan.compute_happiness(tutor_plan, Data().availability[tutor]))

    output_file = str(output_folder) + "/happiness"
    output.plot_happy_and_fair(X, Y, output_file)


if __name__ == "__main__":
    cli.main(prog_name=f"python -m {__package__}")
