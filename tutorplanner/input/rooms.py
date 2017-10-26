__author__ = ("Alexander Elvers <aelvers AT inet.tu-berlin.de>, "
              "Matthias Rost <mrost AT inet.tu-berlin.de>")

__all__ = [
    "Room",
    "import_rooms_from_csv",
    "export_rooms_to_csv",
    "export_rooms_to_xlsx",
]

import csv
import datetime
import warnings
from typing import Union, Dict, Set, List, Optional, Sequence, Iterable, cast

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name

from ..util import settings


time_slots = [10, 12, 14, 16]
hours = range(10, 19)

STARTING_DAY = 1  # Class starts on a Tuesday


class Room:
    """
    A room contains a name and booked slots.
    """

    name: str
    booked: Dict[datetime.date, Set[int]]
    type: str
    capacity: int
    projector: bool

    def __init__(self, name: str) -> None:
        """
        Create room by room name. Initially, no slots are booked.
        """
        # room name
        self.name = name
        # booked time slots
        self.booked = {}
        # room info
        info = settings.get_room_info(name)
        self.type = cast(str, info["type"])
        self.capacity = cast(int, info["capacity"])
        self.projector = cast(bool, info["projector"])

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Room({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Room):
            return self.name == other.name
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def book(self, date: datetime.date, time: int) -> None:
        """
        Book a slot at a date and a time
        """
        self.booked.setdefault(date, set()).add(time)

    def is_booked(self, date: datetime.date, time: int) -> bool:
        """
        Returns if a slot is booked.
        """
        return time in self.booked.get(date, set())

    def get_booked_times(self, date: datetime.date) -> Sequence[int]:
        """
        Returns the time slots the room is booked at the given date.
        """
        return sorted(self.booked.get(date, set()))

    def print_booked_time_slots(self) -> None:
        """
        Print all booked times for this room.
        """
        for date, booked_times in sorted(self.booked.items()):
            for time in sorted(booked_times):
                print(f"Raum {self.name} ist gebucht am {date} um {time} Uhr.")


def import_rooms_from_csv(file: str, initial_rooms: Optional[Iterable[Room]] = None) -> List[Room]:
    """
    Create rooms and set room bookings from a file, separated by tabs. The
    format is described in export_rooms_to_file.

    If initial_rooms is given, it reuses the existing rooms.
    """
    rooms: Dict[str, Room]
    if initial_rooms is None:
        rooms = {}
    else:
        rooms = {room.name: room for room in initial_rooms}
    with open(file) as f:
        reader = csv.reader(f, delimiter="\t")
        lines: List[List[str]] = list(reader)
        day: Optional[datetime.date] = None
        room_names: List[str] = []
        while lines:
            line = lines.pop(0)
            if not any(line):
                day = None
                room_names = []
            elif day is None:
                # header
                day = datetime.datetime.strptime(line[0], "%Y-%m-%d").date()
                room_names = line[1:]
                # create rooms if they don't exist
                for room_name in room_names:
                    if not room_name:  # ignore rooms with empty name
                        continue
                    if room_name not in rooms:
                        rooms[room_name] = Room(room_name)
            else:
                time = int(line[0])
                bookings = line[1:]
                # iterate only the existing rooms
                for booking, room_name in zip(bookings, room_names):
                    if not room_name:  # ignore rooms with empty name
                        continue
                    if booking and booking != "0":
                        rooms[room_name].book(day, time)
    return list(rooms.values())


def export_rooms_to_csv(file: str, rooms: Iterable[Room]) -> None:
    """
    Save room bookings to file, separated by tabs. Each day is represented by a
    block. Blocks are separated by an empty line. Each block contains a date in
    the top left cell, sorted room names as column names, sorted times as row
    headers and an 'x' in the other cells if the room is booked and nothing
    (empty string) if not.
    """
    days_data: List[List[str]] = []
    for day in settings.settings.days():
        day_data = get_export_day_data(day, rooms)
        if not day_data:
            continue
        if days_data:
            days_data.append([])
        days_data.extend(day_data)

    with open(file, "w") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(days_data)


def export_rooms_to_xlsx(file: str, rooms: Iterable[Room], export_capacity: bool = False, maximal_tutorial_size: Optional[int] = None) -> None:
    """
    Save room bookings to file, separated by tabs. Each day is represented by a
    block. Blocks are separated by an empty line. Each block contains a date in
    the top left cell, sorted room names as column names, sorted times as row
    headers and an 'x' in the other cells if the room is booked and nothing
    (empty string) if not.
    """
    times = settings.settings.times._or([])()
    days_data: List[List[str]] = []
    for day in settings.settings.days():
        day_data = get_export_day_data_full_table(day,
                                                  rooms,
                                                  times=times,
                                                  usage_char="1",
                                                  export_capacity=export_capacity,
                                                  maximal_tutorial_size=maximal_tutorial_size)
        if not day_data:
            continue
        if days_data:
            days_data.append([])
        days_data.extend(day_data)

    workbook = xlsxwriter.Workbook(file)
    worksheet = workbook.add_worksheet()

    def parse(string: str) -> Union[str, float]:
        try:
            return float(string)
        except:
            return string

    for row_index, line in enumerate(days_data):
        for column_index, data in enumerate(line):
            worksheet.write(row_index, column_index, parse(data))

    max_column = max([len(line) for line in days_data]) + 10
    max_row = len(days_data)

    format_red = workbook.add_format({'bg_color': '#FF0000',
                                      'font_color': '#000000'})
    format_yellow = workbook.add_format({'bg_color': '#E3DC19',
                                         'font_color': '#000000'})
    format_green = workbook.add_format({'bg_color': '#31C920',
                                        'font_color': '#000000'})

    def conditional_format(cell, expected, minimum, maximum, color):
        worksheet.conditional_format(cell, dict(type="cell", criteria="between", format=color,
                                                minimum=round(minimum * expected),
                                                maximum=round(maximum * expected)))

    if export_capacity:
        # use expected number of students
        expected = settings.settings.expected_number_of_students._or(1000)()
    else:
        # use expected number of rooms
        expected = settings.settings.expected_number_of_rooms._or(26)()

    for row_index in range(max_row+1):
        mod = row_index % (len(times)+2)
        if mod != 0 and mod != len(times) +1:
            start_cell = xl_rowcol_to_cell(row_index, 1)
            end_cell = xl_rowcol_to_cell(row_index, max_column-1)
            worksheet.write_formula(row_index, max_column, f"=SUM({start_cell}:{end_cell})")
        if mod == len(times) + 1:
            start_cell = xl_rowcol_to_cell(row_index-4, max_column)
            end_cell = xl_rowcol_to_cell(row_index-1, max_column)
            worksheet.write_formula(row_index, max_column + 1, f"=SUM({start_cell}:{end_cell})")
            start_cell = xl_rowcol_to_cell(row_index-4, max_column)
            end_cell = xl_rowcol_to_cell(row_index-1, max_column)
            worksheet.write_formula(row_index, max_column + 2, f"=2*SUM({start_cell}:{end_cell})")
            current_cell = xl_rowcol_to_cell(row_index, max_column+2)
            conditional_format(current_cell, expected, 0, .7, format_red)
            conditional_format(current_cell, expected, .7, 1, format_yellow)
            conditional_format(current_cell, expected, 1, 1000, format_green)

    for column in range(max_column):
        column_name = xl_col_to_name(column)
        if column == 0:
            worksheet.set_column(f"{column_name}:{column_name}", 12)
        elif column < max_column:
            worksheet.set_column(f"{column_name}:{column_name}", 10)

    workbook.close()


def get_export_day_data(day: datetime.date, rooms: Iterable[Room], usage_char: str = "x") -> List[List[str]]:
    """
    Returns block data (list of lists of strings) as described in
    export_rooms_to_csv.
    """
    day_rooms: Set[Room] = set()
    day_bookings: Dict[int, Set[str]] = {}
    for room in rooms:
        for time in room.get_booked_times(day):
            day_bookings.setdefault(time, set()).add(str(room))
            day_rooms.add(room)
    if not day_rooms:
        return []

    sorted_day_rooms = sorted(map(str, day_rooms))
    day_data = [[str(day)] + sorted_day_rooms]
    for time in sorted(day_bookings):
        day_data.append([time] + [usage_char * (room in day_bookings[time]) for room in sorted_day_rooms])
    return day_data


def get_export_day_data_full_table(day: datetime.date, rooms: Iterable[Room], times: Sequence[int], usage_char: str = "x", export_capacity: bool = False, maximal_tutorial_size: Optional[int] = None) -> List[List[str]]:
    """
    Returns block data (list of lists of strings) similar to
    get_export_day_data, but with the option to export the capacity and maximal
    tutorial size.
    """
    if export_capacity and maximal_tutorial_size is None:
        maximal_tutorial_size = 10000000
        warnings.warn(f"Hope that not more than {maximal_tutorial_size} many students fit into a room")

    day_rooms: Set[Room] = set()
    day_bookings: Dict[int, Set[str]] = {}
    for room in rooms:
        for time in room.get_booked_times(day):  # TODO: iterate through *all* given times
            day_bookings.setdefault(time, set()).add(str(room))
            day_rooms.add(room)
    for time in times:
        if time not in day_bookings:
            day_bookings[time] = set()

    sorted_day_rooms = sorted(map(str, day_rooms))
    day_data = [[str(day)] + sorted_day_rooms]

    forbidden_timeslots = cast(Dict[datetime.date, Sequence[int]], settings.settings.forbidden_timeslots._or({})())

    for time in sorted(day_bookings):
        if time in forbidden_timeslots.get(day, []):
            if not export_capacity:
                day_data.append([time] + [False] * len(sorted_day_rooms))
            else:
                day_data.append([time] + [0] * len(sorted_day_rooms))
        else:
            if not export_capacity or maximal_tutorial_size is None:
                day_data.append([time] + [usage_char * (room in day_bookings[time]) for room in sorted_day_rooms])
            else:
                # TODO: let day_rooms be a list of rooms and not a list of strings, so that room.capacity can be used
                day_data.append([time] + [min(maximal_tutorial_size, settings.get_room_info(room)["capacity"]) if room in day_bookings[time] else 0 for room in sorted_day_rooms])
    return day_data
