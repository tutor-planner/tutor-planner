__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

__all__ = ["parse_files"]

import datetime
import traceback
from typing import Dict, Optional, Tuple, Iterable, Iterator, Container, Sequence

import bs4

from .rooms import Room, time_slots


SHORT_WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
WORK_DAYS = ("Mo", "Di", "Mi", "Do", "Fr")


def parse_lsf_date(date: str) -> datetime.date:
    """
    Parse a date of the format %d.%m.%Y.
    """
    return datetime.datetime.strptime(date, "%d.%m.%Y").date()


def parse_lsf_time(time: str) -> datetime.time:
    """
    Parse a time of the format %H:%M.
    """
    return datetime.datetime.strptime(time, "%H:%M").time()


def parse_lsf_weekday(weekday: str) -> Optional[int]:
    """
    Parse a weekday.

    Monday == 0 ... Sunday == 6
    """
    try:
        return SHORT_WEEKDAYS.index(weekday)
    except ValueError:
        return None


def filter_date_range(start: datetime.date, end: datetime.date, weekday: Optional[int] = None) -> Iterator[datetime.date]:
    """
    Filter date range by weekday. Returns all dates, starting from start and ending with end, that satisfy the weekday.

    If weekday is None, returns all dates except weekend (Saturday, Sunday).
    """
    date = start
    while date <= end:
        if weekday is None and SHORT_WEEKDAYS[date.weekday()] in WORK_DAYS or date.weekday() == weekday:
            yield date
        date += datetime.timedelta(days=1)


def filter_time_range(start: int, end: int, time_slots: Optional[Container[int]] = None) -> Iterator[int]:
    """
    Filter time range by time slots. Returns all times, starting from start and ending before end, that are contained
    in time_slots.

    If time_slots is not given, returns all hours in the range.

    Only works with full hours.
    """
    if time_slots is None:
        time_slots = range(24)
    for time in range(start, end):
        if time in time_slots:
            yield time


def get_room_names(soup: bs4.BeautifulSoup) -> Iterable[str]:
    """
    Get the names of all rooms in the file.
    """
    return set(x.string for x in soup.Lecture.find_all("RaumBez"))


def get_bookings(soup: bs4.BeautifulSoup) -> Iterable[Tuple[str, datetime.date, int]]:
    """
    Get the time slots when a room is booked.

    Returns tuples of (room_name, date, time).
    """
    for term in soup.find_all("Terms"):
        try:
            if not term.TerBeginn.string and not term.TerBeginDat.string:
                continue
            start_time = parse_lsf_time(term.TerBeginn.string)
            end_time = parse_lsf_time(term.TerEnde.string)
            start_date = parse_lsf_date(term.TerBeginDat.string)
            end_date = parse_lsf_date(term.TerEndeDat.string)
            frequency = term.TerRhyth.string
            weekday = parse_lsf_weekday(term.find("WoTag").string)
            room_names = [room.RaumBez.string for room in term.find_all("Rooms", recursive=False)]
            step = 1  # step size for date selection
            if frequency == "Einzel":
                assert start_date == end_date
                assert weekday is None or start_date.weekday() == weekday
            elif frequency.endswith("chentl"):  # wöchentl
                assert weekday is not None
            elif frequency.startswith("14t"): # 14tägl
                assert weekday is not None
                step = 2
            else:
                assert frequency == "Block"
                assert weekday is None
            dates = list(filter_date_range(start_date, end_date, weekday))[::step]
            times = list(filter_time_range(start_time.hour, end_time.hour, time_slots))
            for room_name in room_names:
                for date in dates:
                    for time in times:
                        yield room_name, date, time
        except:
            print("WARNING:\n--- Parsing error in ---")
            print(term)
            print("---")
            print(traceback.format_exc(), end="")
            print("--- END OF WARNING ---")


def parse_files(files: Iterable[str], initial_rooms: Optional[Iterable[Room]] = None) -> Sequence[Room]:
    """
    Parse all files and return rooms with bookings.

    If rooms is given, it reuses the existing rooms.
    """
    rooms: Dict[str, Room]
    if initial_rooms is None:
        rooms = {}
    else:
        rooms = {room.name: room for room in initial_rooms}
    for file in files:
        with open(file) as f:
            soup = bs4.BeautifulSoup(f, "lxml-xml")
            room_names = get_room_names(soup)
            # for room_name in room_names:
            #     rooms[room_name] = Room(room_name)
            for room_name, date, time in get_bookings(soup):
                if room_name not in rooms:
                    rooms[room_name] = Room(room_name)
                rooms[room_name].book(date, time)
    return list(rooms.values())
