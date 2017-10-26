__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "get_active_plan_dict",
    "get_rooms_by_day",
    "check_plan",
    "get_schedule_per_tutor",
    "get_tutorials_by_time",
    "get_tutorials_for_tickets",
    "get_extended_tutorials_for_tickets",
    "get_events_by_time",
    "get_course_leaders",
]

import csv
import pickle
from collections import defaultdict
from typing import List, Dict, Tuple, Any, TypeVar

from .input.data import Data
from .input.plan import PersonalPlanDict, get_plan_paths
from .util import converter, settings
from .util.settings import TUTORIUM


T = TypeVar("T")


def latex_fix(obj: T) -> T:
    """
    Escape strings for LaTeX.
    """
    # FIXME catch all of them
    if hasattr(obj, "replace"):
        # obj = obj.replace("\\", "{\\textbackslash}")
        # obj = obj.replace("~", "{\\textasciitilde}")
        obj = obj.replace("_", "\\_")
    return obj


def get_active_plan_dict() -> PersonalPlanDict:
    """
    Get active plan.
    """
    path = get_plan_paths()["active"] / "personalPlans_Rooms.pickle"
    with open(path, "rb") as f:
        plan = pickle.load(f)
    check_plan(plan)
    return plan


def get_rooms_by_day() -> Dict[int, Dict[str, Dict[int, Tuple[str, str]]]]:
    """
    Returns a dictionary of day -> room -> time -> event, where event is a tuple
    of a tutor's last name and one of the values RechneruebungMAR, RechneruebungTEL,
    Kontrolle, Tutorium.
    """
    plan = get_active_plan_dict()
    rooms: Dict[int, Dict[str, Dict[int, Tuple[str, str]]]] = {}
    for tutor in plan:
        for task, schedule in plan[tutor].items():
            for day, times in schedule.items():
                if not day in rooms:
                    rooms[day] = {}
                for time, room in times.items():
                    if room:
                        if not room in rooms[day]:
                            rooms[day][room] = {}
                        rooms[day][room].update({time:(latex_fix(tutor), task)})
    return rooms


def check_plan(plan: PersonalPlanDict) -> None:
    """
    Some sanity checks for the plan:
        - No tutor is double-booked at any time
        - No tutor has an appointment when unavailable
    """
    for tutor_name in plan:
        for task in plan[tutor_name]:
            for day in plan[tutor_name][task]:
                for time in plan[tutor_name][task][day]:
                    # Check if tutor is planned for multiple simultaneous events:
                    simultaneous_tasks = [task for task in settings.TASKS
                                          if bool(plan[tutor_name][task][day][time])]
                    if len(simultaneous_tasks) > 1:
                        raise ValueError(f"Tutor {tutor_name} hat am {day}. Tag um {time} Uhr mehrere Aufgaben:\n"
                                         + " ".join(simultaneous_tasks))

                    # Check if tutor is booked for an unavailable slot:
                    if bool(plan[tutor_name][task][day][time]):
                        time = max(t1 for t1 in [10, 12, 14, 16] if t1 <= time)
                        avail = Data().tutor_by_name[tutor_name].availability[converter.day_index_to_date(day)][time]
                        if avail is None or avail < 1:
                            raise ValueError(f"Tutor {tutor_name} hat am {day}. Tag um {time} Uhr keine Zeit")


def get_schedule_per_tutor() -> Dict[str, List[Dict[str, Any]]]:
    def weekday(day: int) -> str:
        days = {1:"Montag",
                2:"Dienstag",
                3:"Mittwoch",
                4:"Donnerstag",
                5:"Freitag",
                6:"Montag",
                7:"Dienstag",
                8:"Mittwoch",
                9:"Donnerstag",
                10:"Freitag"}
        return days[day]

    plan = get_active_plan_dict()
    tutor_sched: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tutor in plan:
        for task, schedule in plan[tutor].items():
            for day, times in schedule.items():
                for time, room in times.items():
                    if room:
                        tutor_sched[tutor].append(dict(
                            task=task,
                            time=time,
                            day=day,
                            weekday=weekday(day),
                            room=room,
                        ))

    return tutor_sched


def get_tutorials_by_time() -> Dict[int, Dict[int, List[Tuple[str, str]]]]:
    """
    Returns a dictionary of all tutorial events with the keys day -> time -> list of events, where events
    are tuples of the room name and the tutor's last name.
    """
    plan = get_active_plan_dict()
    tutorials: Dict[int, Dict[int, List[Tuple[str, str]]]] = defaultdict(dict)
    for tutor in plan:
        for day, times in plan[tutor][TUTORIUM].items():
            for time, room in times.items():
                if room:
                    if not time in tutorials[day].keys():
                        tutorials[day][time] = [(room, tutor)]
                    else:
                        tutorials[day][time].append((room, tutor))
    return tutorials


def get_tutorials_for_tickets() -> Dict[int, List[Tuple[int, str, str]]]:
    """
    Returns a dict of tutorials in format day -> list of events, where events
    are tuples of the time, room name and the tutor's last name.
    """
    plan = get_active_plan_dict()
    tutorials: Dict[int, List[Tuple[int, str, str]]] = defaultdict(list)
    for tutor in plan:
        for day, times in plan[tutor][TUTORIUM].items():
            for time, room in times.items():
                if room:
                    tutorials[day].append((time, room, tutor))
    return tutorials


def get_extended_tutorials_for_tickets() -> Dict[int, Dict[int, Dict[str, List[str]]]]:
    """
    Returns a dict of tutorials in format day -> time -> room name -> list of tutors' last names.
    The tutor names are escaped.
    """
    plan = get_active_plan_dict()
    tutorials: Dict[int, Dict[int, Dict[str, List[str]]]] = {}
    for tutor in plan:
        for task in settings.TASKS:
            for day, times in plan[tutor][task].items():
                if day not in tutorials:
                    tutorials[day] = {}
                for time, room in times.items():
                    if room:
                        if time not in tutorials[day]:
                            tutorials[day][time] = {}
                        if room not in tutorials[day][time]:
                            tutorials[day][time][room] = []
                        tutorials[day][time][room].append(latex_fix(tutor))

    return tutorials


def get_events_by_time() -> Dict[int, Dict[int, List[Tuple[str, str, str]]]]:
    """
    Returns a dictionary of all events with the keys day -> time -> list of events, where events
    are tuples of the event type (RechneruebungMAR, RechneruebungTEL, Kontrolle, or Tutorium),
    the room name and the tutor's last name
    """
    plan = get_active_plan_dict()
    events: Dict[int, Dict[int, List[Tuple[str, str, str]]]] = {}
    for tutor in plan:
        for task in plan[tutor]:
            for day, times in plan[tutor][task].items():
                if not day in events:
                    events[day] = {}
                for time, room in times.items():
                    if room:
                        if not time in events[day].keys():
                            events[day][time] = [(task, room, tutor)]
                        else:
                            events[day][time].append((task, room, tutor))
    return events


def get_course_leaders() -> List[Dict[str, str]]:
    """
    Return a list of all associated WMs.
    """
    # first_name, last_name, email, phone
    filename: str = settings.settings.paths.course_leaders()
    if filename is None:
        return []
    with open(filename) as f:
        wm_list = list(csv.DictReader(f, dialect="excel-tab"))
    return sorted(wm_list, key=lambda wm: wm["last_name"])
