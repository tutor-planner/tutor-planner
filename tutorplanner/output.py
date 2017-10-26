__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "render_latex",
    "render_format",
    "render_pdf",
    "render_html",
    "render_template",
    "compute_tutorial_sizes",
    "get_room_dictionary",
    "plot_happy_and_fair",
]

import datetime
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional, Tuple, Any, Iterable, Dict, List

import click
import matplotlib.pyplot as plt
from mako.template import Template, exceptions

from . import read_pickled_files as rpf
from .input.data import Data
from .input.rooms import import_rooms_from_csv
from .util import converter, settings

DEBUG = True
TEMPLATE_DIR = pathlib.Path(settings.settings.paths._get("templates", "templates")()).resolve()
PDF_DIR = pathlib.Path(settings.settings.paths._get("pdf_output", "pdf")()).resolve()
PNG_DIR = pathlib.Path(settings.settings.paths._get("png_output", "png")()).resolve()
HTML_DIR = pathlib.Path(settings.settings.paths._get("html_output", "html")()).resolve()


def err_print(msg: str) -> None:
    print("ERROR:", msg, file=sys.stderr)


def dbg_print(msg: str) -> None:
    if DEBUG:
        print("DEBUG:", msg, file=sys.stderr)


def date_to_string(date: datetime.date) -> str:
    """
    Format date with weekday.
    """
    return f"{settings.weekdays[date.weekday()]}, {date:%d.%m.}"  # TODO: use locale


def day_index_to_string(day_index: int) -> str:
    """
    Format day index with weekday.
    """
    return date_to_string(converter.day_index_to_date(day_index))


# rendering functions

def render_latex(tex_data: str, filename: str, output_pdf: bool = False, output_html: bool = False,
                 output_png: bool = False) -> None:
    """
    Render tex_data data and return the rendered data.

    :param tex_data: the tex_data data
    :param filename: the output filename
    :param output_pdf: if enabled, write PDF output
    :param output_html: if enabled, write HTML output
    :param output_png: if enabled, write PNG output
    """
    if output_pdf or output_png:
        PDF_DIR.mkdir(exist_ok=True)
        pdf_file = PDF_DIR / f"{filename}.pdf"

        pdf = render_pdf(tex_data)
        pdf_file.write_bytes(pdf)

        if output_png:
            PNG_DIR.mkdir(exist_ok=True)
            png_file = PNG_DIR / f"{filename}.png"
            crop_file = PDF_DIR / f"{filename}-crop.pdf"

            args = ["pdfcrop", str(pdf_file)]
            dbg_print(f"Running: {' '.join(map(str, args))}")
            subprocess.run(args, check=True)

            args = ["convert", "-density", "600", crop_file,
                    "-quality", "100", "-background", "white", "-alpha", "remove", png_file]
            dbg_print(f"Running: {' '.join(map(str, args))}")
            subprocess.run(args)

            crop_file.unlink()

    if output_html:
        HTML_DIR.mkdir(exist_ok=True)
        html, css = render_html(tex_data)
        (HTML_DIR / f"{filename}.html").write_bytes(html.replace(b"render.css", f"{filename}.css".encode()))
        (HTML_DIR / f"{filename}.css").write_bytes(css)


def render_format(
        tex_data: str, command: List[Any], output_formats: Iterable[str],
        resources: Optional[str] = None) -> List[bytes]:
    """
    Render tex data with custom command into output formats and return the rendered data.

    :param tex_data: the tex data
    :param command: command to execute; ``None`` is replaced by the tex filename
    :param output_formats: the tex data
    :param resources: directory of additional resources
    """
    with tempfile.TemporaryDirectory() as d:
        temp_dir = pathlib.Path(d)
        dbg_print(f"Created temp dir at {temp_dir}")

        temp_tex = temp_dir / "render.tex"

        if resources:
            dbg_print("Copying additional resources")
            for resource_file in (TEMPLATE_DIR / resources).iterdir():
                shutil.copy(resource_file, temp_dir)

        dbg_print(f"Compiling template {temp_tex}")
        temp_tex.write_text(tex_data)

        command[command.index(None)] = temp_tex
        dbg_print(f"Running: {' '.join(map(str, command))}")
        subprocess.run(command, check=True, cwd=temp_dir)

        return [temp_tex.with_suffix("." + suffix).read_bytes() for suffix in output_formats]


def render_pdf(tex_data: str, resources: Optional[str] = None) -> bytes:
    """
    Render tex data as PDF and return the rendered data.

    :param tex_data: the tex data
    :param resources: directory of additional resources
    """
    mime_data = render_format(tex_data, ["pdflatex", None, "-halt-on-error"], ["pdf"], resources)
    return mime_data[0]


def render_html(tex_data: str, resources: Optional[str] = None) -> Tuple[bytes, bytes]:
    """
    Render tex data as HTML and return the rendered data.

    :param tex_data: the tex data
    :param resources: directory of additional resources
    """
    tex_data = tex_data.replace("scrartcl", "article")
    mime_data = render_format(tex_data, ["htlatex", None], ["html", "css"], resources)
    return mime_data[0], mime_data[1]


def render_template(path: pathlib.Path, **kwargs: Any) -> str:
    """
    Make tex template.

    :param path: template file
    :param kwargs: template data
    """
    template = Template(
        filename=str(path),
        default_filters=['decode.utf8', 'l'],
        input_encoding='utf-8',
        output_encoding='utf-8',
        preprocessor=lambda x: re.sub(r'\\\\', r"${'\\\\\\\'}", x),
        imports=[
            'from tutorplanner.read_pickled_files import latex_fix as l',
            'from tutorplanner.output import day_index_to_string'
        ],
    )
    try:
        return template.render_unicode(**kwargs)
    except:
        print(exceptions.text_error_template().render())
        raise


# helper functions

def compute_tutorial_sizes(tutorials: Iterable[Tuple[int, str, str]],
                           seats_targeted: int,
                           seats_with_overflow: int,
                           maximal_standard_overflow_size: int,
                           standard_tutorial_size: int) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    This function computes for each tutorial_room the number of regular tickets and the number of overflow tickets that
    shall be created. Concretely, this function works as follows:

    #. According to an (initially small) default tutorial size the number of seats per room are set.
    #. If the number of regular tutorial seats is not reached, the tutorial size is increased. Note that in this first
       step the number of seats per tutorial will not lie about the room's capacity.
    #. By increasing the default tutorial size, either the number of regular tickets can be provisioned and the next
       stage computes overflow tickets for each room. On the other hand, if this is not possible an exception is thrown.

    Assuming that the regular tickets have been created, the algorithm then generates overflow tickets, such that
    the number of seats reaches at least seats_with_overflow. This works as follows:

    #. Overflow tickets are created for all rooms which have not yet passed the maximal_overflow_capacity.
    #. Overflow tickets are created for all rooms independently of whether the maximal capacity is violated or not.

    :param tutorials: the tutorials as tuples of time, room name, tutor name
    :param seats_targeted:
    :param seats_with_overflow:
    :param maximal_standard_overflow_size:
    :param standard_tutorial_size:
    :return: ``room_seats_standard`` and ``room_seats_overflow`` that are mappings from room name to number of seats
    """
    room_seats_standard: Dict[str, int] = {}
    room_seats_overflow: Dict[str, int] = {}

    max_overflow_capacity: Dict[str, int] = {}
    max_capacity: Dict[str, int] = {}
    number_of_tutorials_in_room: Dict[str, int] = {}

    available_number_of_seats = 0
    old_available_number_of_seats = 0

    sufficiently_many_seats_available = False
    while not sufficiently_many_seats_available:

        for (hour, room, tutor) in tutorials:
            if room not in room_seats_standard.keys():
                room_info = settings.get_room_info(room)
                max_overflow_capacity[room] = min(maximal_standard_overflow_size, room_info["capacity"])
                max_capacity[room] = min(standard_tutorial_size, room_info["capacity"])
                room_seats_standard[room] = min(standard_tutorial_size, max_capacity[room])
                room_seats_overflow[room] = 0
                number_of_tutorials_in_room[room] = 0

            number_of_tutorials_in_room[room] += 1
            available_number_of_seats += room_seats_standard[room]

        if available_number_of_seats < seats_targeted:
            if old_available_number_of_seats == available_number_of_seats:
                raise Exception("Cannot possibly place reach the targeted number of seats")

            standard_tutorial_size += 1

            room_seats_standard.clear()
            room_seats_overflow.clear()
            max_overflow_capacity.clear()
            max_capacity.clear()
            number_of_tutorials_in_room.clear()
            old_available_number_of_seats = available_number_of_seats
            available_number_of_seats = 0

        else:
            sufficiently_many_seats_available = True

    print(f"Standard tutorial size is {standard_tutorial_size}")

    overflow_seats_to_generate = seats_with_overflow - available_number_of_seats

    print(f"need to generate {overflow_seats_to_generate} many overflow seats")

    progress = True
    while progress and overflow_seats_to_generate > 0:
        progress = False
        for room in room_seats_standard.keys():
            if room_seats_standard[room] + room_seats_overflow[room] < max_overflow_capacity[room]:
                room_seats_overflow[room] += 1
                overflow_seats_to_generate -= number_of_tutorials_in_room[room]
                progress = True

    progress = True
    while progress and overflow_seats_to_generate > 0:
        progress = False
        for room, _ in sorted(room_seats_overflow.items(), key=lambda x: -x[1]):
            room_seats_overflow[room] += 1
            overflow_seats_to_generate -= number_of_tutorials_in_room[room]
            progress = True

    print("Result of tutorial seat assignments...")
    column_format = "{:^12}\t{:^22}\t{:^14}\t{:^14}\t{:^14}\t{:^22}\t{:^22}"
    print(column_format.format(
        "room", "number of tutorials", "std. seats", "overflow seats", "room capacity", "expected seats over cap",
        "max seats over cap"))
    for room in room_seats_standard.keys():
        room_info = settings.get_room_info(room)
        cap: int = room_info["capacity"]
        exp_over_cap = room_seats_standard[room] - cap
        max_over_cap = room_seats_overflow[room] + room_seats_standard[room] - cap

        print(column_format.format(
            room, number_of_tutorials_in_room[room], room_seats_standard[room], room_seats_overflow[room], cap,
            exp_over_cap, max_over_cap))

    sum_standard_seats = sum(number_of_tutorials_in_room[room] * room_seats_standard[room]
                             for room in room_seats_standard.keys())
    sum_overflow_seats = sum(number_of_tutorials_in_room[room] * room_seats_overflow[room]
                             for room in room_seats_standard.keys())
    print("===============")
    print(f"Will provision {sum_standard_seats} many regular seats and {sum_overflow_seats} additional overflow seats")
    print("===============")

    return room_seats_standard, room_seats_overflow


def get_room_dictionary(specific_bookings: bool = False) -> Dict[int, Dict[int, List[str]]]:
    """
    Get a dict that contains rooms by day index and hour.

    If ``specific_bookings`` is enabled, also use bookings from
    ``settings.paths.bookings_additional``.
    """
    if specific_bookings:
        additional_rooms_file = settings.settings.paths.bookings_additional()
        if not additional_rooms_file:
            return {}
        all_rooms = import_rooms_from_csv(additional_rooms_file)
    else:
        all_rooms = Data().room_by_name.values()

    all_times: List[int] = settings.settings.times()
    bookings: Dict[int, Dict[int, List[str]]] = {}
    days: List[datetime.date] = settings.settings.days()
    for day in days:
        day_index = converter.date_to_day_index(day)
        bookings[day_index] = {}
        for hour in all_times:
            bookings[day_index][hour] = []
        for room in all_rooms:
            # if room.type == "tutorial":
            times = room.get_booked_times(day)
            for hour in times:
                bookings[day_index][hour].append(room.name)
    return bookings


# command line interface

@click.group()
def cli():
    """
    Generate pdf files or other formats.
    """


@cli.command("tutor-schedule")
@click.argument("day")
@click.option("--fontsize", default=12)
@click.option("--bottom", default=3.5)
@click.option("--top", default=2.5)
@click.option("--pdf/--no-pdf", "output_pdf", is_flag=True, default=True)
@click.option("--html", "output_html", is_flag=True, default=False)
@click.option("--first-names", is_flag=True, default=False)
def make_tutor_schedule(day, fontsize, bottom, top, output_pdf, output_html, first_names):
    """
    Output a daily schedule for all tutors over all rooms.
    """
    days = settings.settings.days._or([])()
    days_dict = dict([(f"{d:%m-%d}", d) for d in days] + [(f"{d:%Y-%m-%d}", d) for d in days])
    if day not in days_dict:
        raise click.BadParameter(f"invalid choice {day}. (choose from {', '.join(days_dict.keys())})")
    day = days_dict[day]
    day_index = converter.date_to_day_index(day)

    filename = f"tutor_schedule_{day}"
    if first_names:
        filename += "_first_names"
    else:
        filename += "_last_names"
    path = TEMPLATE_DIR / "tutor_schedule.tex.mako"
    rooms = rpf.get_rooms_by_day()[day_index]
    tutorials = rpf.get_tutorials_for_tickets()[day_index]

    hours = settings.settings.times()
    lower = hours[0]
    upper = hours[-1] + 2

    external_rooms = ["MAR 4.033", "MAR 6.004", "MAR 6.011", "MAR 6.051"]
    room_bookings = converter.to_single_hour_precision(get_room_dictionary())[day_index]
    print(room_bookings)
    purged_bookings = {}
    for hour, room_list in room_bookings.items():
        purged_bookings[hour] = [room for room in room_list if room not in external_rooms]
    print(tutorials)
    print(rooms)

    extended_tutorials = rpf.get_extended_tutorials_for_tickets()[day_index]
    print(extended_tutorials)
    for hour in range(lower, upper):
        if hour not in extended_tutorials:
            extended_tutorials[hour] = {}
        for room in rooms:
            if room not in extended_tutorials[hour]:
                extended_tutorials[hour][room] = []

    print(rooms)

    if first_names:
        tutor_name_to_first_name = {last_name: t.first_name for last_name, t in Data().tutor_by_name.items()}

        # convert last names to first names
        for hour in range(lower, upper):
            for room in extended_tutorials[hour]:
                extended_tutorials[hour][room] = [tutor_name_to_first_name[name]
                                                  for name in extended_tutorials[hour][room]]

    tex = render_template(
        path,
        rooms=rooms,
        tutorials=extended_tutorials,
        bookedRooms=purged_bookings,
        dayString=date_to_string(day),
        dayBegin=lower,
        dayEnd=upper,
        numberOfHours=upper - lower,
        fontsize=fontsize,
        bottom=bottom,
        top=top,
    )
    render_latex(tex, filename, output_pdf, output_html)


@cli.command("badges")
@click.option("--pdf/--no-pdf", "output_pdf", is_flag=True, default=True)
@click.option("--html", "output_html", is_flag=True, default=False)
def make_badges(output_pdf, output_html):
    """
    Output badges for tutors and course leaders with their names and roles on it.
    """
    filename = "badges"
    path = TEMPLATE_DIR / "badges.tex.mako"
    tutors = Data().tutor_by_name
    tex = render_template(path, tutors=tutors, wms=rpf.get_course_leaders())
    render_latex(tex, filename, output_pdf, output_html)


@cli.command("tutor-plans")
@click.option("--pdf/--no-pdf", "output_pdf", is_flag=True, default=True)
@click.option("--html", "output_html", is_flag=True, default=False)
def make_tutor_plans(output_pdf, output_html):
    """
    Output a plan for each tutor.
    """
    filename_prefix = "tutor_plan"
    path = TEMPLATE_DIR / "tutor_plan.tex.mako"
    schedules = rpf.get_schedule_per_tutor()
    tutors = Data().tutor_by_name

    first_wm = rpf.get_course_leaders()[0]
    for tutor in tutors:
        tex = render_template(path, tutor_name=rpf.latex_fix(tutor), tutor=tutors[tutor], schedule=schedules[tutor],
                              datum=(time.strftime("%d.%m.%Y %H:%M")), wm=first_wm)
        filename = "_".join([filename_prefix, tutor, tutors[tutor].first_name]).lower()
        render_latex(tex, filename, output_pdf, output_html)


@cli.command("contact-list")
@click.option("--pdf/--no-pdf", "output_pdf", is_flag=True, default=True)
@click.option("--html", "output_html", is_flag=True, default=False)
def make_contact_list(output_pdf, output_html):
    """
    Output a contact list of tutors and course leaders.
    """
    filename = "contact_list"
    path = TEMPLATE_DIR / "contact_list.tex.mako"
    tutors = Data().tutor_by_name
    tex = render_template(path, tutors=tutors, wms=rpf.get_course_leaders())
    render_latex(tex, filename, output_pdf, output_html)


@cli.command("tickets")
@click.argument("day")
@click.option("--seats-regular", "targeted_seats", default=0)
@click.option("--seats-with-overflow", "targeted_seats_with_overflow", default=0)
@click.option("--fontsize", default=12)
@click.option("--bottom", default=3.5)
@click.option("--top", default=2.5)
@click.option("--maximal-overflow-tutorial-size", default=0)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--day-begin", default=10)
@click.option("--day-end", default=18)
@click.option("--pdf/--no-pdf", "output_pdf", is_flag=True, default=True)
@click.option("--html", "output_html", is_flag=True, default=False)
@click.option("--standard-tutorial-size", default=20)
def make_tickets(
        day,
        targeted_seats,
        targeted_seats_with_overflow,
        fontsize,
        bottom,
        top,
        maximal_overflow_tutorial_size,
        dry_run,
        day_begin,
        day_end,
        output_pdf,
        output_html,
        standard_tutorial_size):
    """
    Generate tickets for the students.
    """
    days = settings.settings.days._or([])()
    days_dict = dict([(f"{d:%m-%d}", d) for d in days] + [(f"{d:%Y-%m-%d}", d) for d in days])
    if day not in days_dict:
        raise click.BadParameter(f"invalid choice {day}. (choose from {', '.join(days_dict.keys())})")
    day = days_dict[day]
    day_index = converter.date_to_day_index(day)

    filename = f"tickets_{day}"
    path = TEMPLATE_DIR / "tickets.tex.mako"

    # get daily hours

    # get room bookings
    room_bookings = converter.to_single_hour_precision(get_room_dictionary())[day_index]
    room_bookings_additional = converter.to_single_hour_precision(get_room_dictionary(specific_bookings=True)).get(day_index)

    if room_bookings_additional:
        # merge room bookings
        for hour in room_bookings.keys():
            for room in room_bookings_additional[hour]:
                if room not in room_bookings[hour]:
                    room_bookings[hour].append(room)

    # get plan
    event_plan = rpf.get_events_by_time()[day_index]

    # collect all rooms where supervisioning is happening
    supervised_rooms = {}
    for hour in range(day_begin, day_end):
        supervised_rooms[hour] = set()
        if hour in event_plan:
            for (task, room, tutor) in event_plan[hour]:
                if room not in supervised_rooms[hour]:
                    supervised_rooms[hour].add(room)

    # collect rooms
    pool_rooms = set()
    seminar_rooms = set()
    for hour in range(day_begin, day_end):
        for room in room_bookings[hour]:
            if settings.get_room_info(room)["type"].startswith("exercise"):
                pool_rooms.add(room)
            elif settings.get_room_info(room)["type"] == "tutorial":
                if room in supervised_rooms[hour]:
                    seminar_rooms.add(room)

    # remove smaller exercise rooms from list
    pool_rooms.discard("TEL 103")
    pool_rooms.discard("TEL 109")

    external_rooms = ["MAR 4.033", "MAR 6.004", "MAR 6.011", "MAR 6.051"]

    # remove external rooms from being free to use
    for hour in room_bookings.keys():
        room_bookings[hour] = [room for room in room_bookings[hour]
                               if room not in external_rooms or room in supervised_rooms[hour]]

    tutorials = rpf.get_tutorials_for_tickets()[day_index]
    tutorials = sorted(tutorials, key=lambda entry: entry[0])
    room_seats, overflow_seats = compute_tutorial_sizes(tutorials, targeted_seats, targeted_seats_with_overflow,
                                                        maximal_standard_overflow_size=maximal_overflow_tutorial_size,
                                                        standard_tutorial_size=standard_tutorial_size)

    if not dry_run:
        tex = render_template(
            path,
            seminar_room_names=seminar_rooms,
            pool_room_names=pool_rooms,
            room_bookings=room_bookings,
            supervised_rooms=supervised_rooms,
            tutorials=tutorials,
            roomSeats=room_seats,
            roomSeatsOverflow=overflow_seats,
            dayString=date_to_string(day),
            dayBegin=day_begin,
            dayEnd=day_end,
            numberOfHours=day_end - day_begin,
            fontsize=fontsize,
            bottom=bottom,
            top=top,
        )
        with open("latex", "w") as file:
            file.write(tex)
        render_latex(tex, filename, output_pdf=output_pdf, output_html=output_html)


@cli.command("course-overview")
@click.argument("day")
@click.option("--day-begin", default=10)
@click.option("--day-end", default=18)
@click.option("--fontsize", default=12)
@click.option("--bottom", default=3.5)
@click.option("--top", default=2.5)
@click.option("--pdf/--no-pdf", "output_pdf", is_flag=True, default=True)
@click.option("--html", "output_html", is_flag=True, default=False)
@click.option("--png", "output_png", is_flag=True, default=False)
@click.option("--remove-supervisions", default=None)
def make_course_overview(
        day,
        day_begin,
        day_end,
        fontsize,
        bottom,
        top,
        output_pdf,
        output_html,
        output_png,
        remove_supervisions):
    """
    Output a daily schedule of the course.
    """
    days = settings.settings.days._or([])()
    days_dict = dict([(f"{d:%m-%d}", d) for d in days] + [(f"{d:%Y-%m-%d}", d) for d in days])
    if day not in days_dict:
        raise click.BadParameter(f"invalid choice {day}. (choose from {', '.join(days_dict.keys())})")
    day = days_dict[day]
    day_index = converter.date_to_day_index(day)

    filename = f"course_overview_{day}"
    path = TEMPLATE_DIR / "course_overview.tex.mako"

    # get daily hours

    # get room bookings
    room_bookings = converter.to_single_hour_precision(get_room_dictionary())[day_index]
    room_bookings_additional = converter.to_single_hour_precision(get_room_dictionary(specific_bookings=True)).get(day_index)

    if room_bookings_additional:
        # merge room bookings
        for hour in room_bookings.keys():
            for room in room_bookings_additional[hour]:
                if room not in room_bookings[hour]:
                    room_bookings[hour].append(room)

    # get plan
    event_plan = rpf.get_events_by_time()[day_index]

    external_rooms = ["MAR 4.033", "MAR 6.004", "MAR 6.011", "MAR 6.051"]

    # collect all rooms where supervisioning is happening
    supervised_rooms = {}
    for hour in range(day_begin, day_end):
        supervised_rooms[hour] = set()
        if hour in event_plan:
            for (task, room, tutor) in event_plan[hour]:
                if room not in supervised_rooms[hour]:
                    supervised_rooms[hour].add(room)

    # collect rooms
    pool_rooms = set()
    seminar_rooms = set()
    for hour in range(day_begin, day_end):
        for room in room_bookings[hour]:
            if settings.get_room_info(room)["type"].startswith("exercise"):
                pool_rooms.add(room)
            elif settings.get_room_info(room)["type"] == "tutorial":
                if room in supervised_rooms[hour]:
                    seminar_rooms.add(room)

    # remove smaller exercise rooms from list
    pool_rooms.discard("TEL 103")
    pool_rooms.discard("TEL 109")

    if remove_supervisions is not None:
        list_of_removals = remove_supervisions.split(";")

        for removal in list_of_removals:
            temp = removal.split(":")
            hour = int(temp[0])
            removed_room = temp[1]
            print(f"{hour}: {room}")  # TODO: room seems wrong here
            supervised_rooms[hour] = [room for room in supervised_rooms[hour] if room != removed_room]

    # remove external rooms from being free to use
    for hour in room_bookings.keys():
        room_bookings[hour] = [room for room in room_bookings[hour]
                               if room not in external_rooms or room in supervised_rooms[hour]]

    # rooms = rpf.get_rooms_by_day()[day]
    tutorials = rpf.get_tutorials_for_tickets()[day_index]
    tutorials = sorted(tutorials, key=lambda entry: entry[0])
    # external_rooms = ["MAR 4.033", "MAR 6.004", "MAR 6.011", "MAR 6.051"]

    tex = render_template(
        path,
        seminar_room_names=seminar_rooms,
        pool_room_names=pool_rooms,
        room_bookings=room_bookings,
        supervised_rooms=supervised_rooms,
        tutorials=tutorials,
        dayString=date_to_string(day),
        dayBegin=day_begin,
        dayEnd=day_end,
        numberOfHours=day_end - day_begin,
        fontsize=fontsize,
        bottom=bottom,
        top=top,
    )

    render_latex(tex, filename, output_pdf=output_pdf, output_html=output_html, output_png=output_png)


def plot_happy_and_fair(x, y, filename):
    """
    Scatter work happiness.
    """
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    ax.set_xlabel("Effektive Praesenzzeit der Arbeitszeit[%]")
    ax.set_ylabel("Happiness (1: nicht happy; 3: sehr happy)")
    plt.scatter(x, y, color='red', s=20, edgecolor='black')
    plt.savefig(filename + '.png')
