__author__ = "Alexander Elvers <aelvers AT inet.tu-berlin.de>"

__all__ = ["Tutor", "load_tutors"]

import csv
import datetime
import locale
import pathlib
import traceback
from typing import Dict, Sequence, Optional, cast, Tuple, List, Union

from ..util import settings


class Tutor:
    """
    A tutor of the course.
    """
    last_name: str
    first_name: str
    email: str
    department: str
    phone: str
    monthly_work_hours: int
    max_hours_without_break: int
    max_tutorials_without_break: int
    knowledge: int
    unsure_about_second_week: int
    availability: Dict[datetime.date, Dict[int, Optional[int]]]

    def __str__(self) -> str:
        if hasattr(self, "first_name"):
            return f"{self.first_name} {self.last_name}"
        else:
            return f"{self.last_name}"

    def __repr__(self) -> str:
        return f"Tutor({self.last_name}, {self.first_name})"

    def __hash__(self) -> int:
        return hash((self.last_name, self.first_name))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Tutor):
            return (self.last_name, self.first_name) == (other.last_name, other.first_name)
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    @classmethod
    def load_from_file(cls, filename: str) -> "Tutor":
        fields = ("last_name", "first_name", "email", "department", "phone",
                  "monthly_work_hours", "max_hours_without_break", "max_tutorials_without_break",
                  "knowledge", "unsure_about_second_week")

        # split days by week and load times
        days = cast(Sequence[datetime.date], settings.settings.days())
        days_by_week: Dict[Tuple[int, int], List[datetime.date]] = {}
        for day in days:
            days_by_week.setdefault(day.isocalendar()[:2], []).append(day)
        times = cast(Sequence[int], settings.settings.times())

        locale.resetlocale()  # fix missing locale bug
        lines: List[str]
        with open(filename) as f:
            dialect = csv.Sniffer().sniff(f.read(50).split("\n")[0])
            f.seek(0)
            reader = csv.reader(f, dialect)
            lines = list(reader)
        if len(lines) < len(fields) + (3 + len(times)) * (len(days_by_week)):
            raise ValueError(f"cannot parse {filename}: too few lines")

        def invalid_entry(message: str) -> ValueError:
            e = ValueError(message)
            e.tutor = tutor
            return e

        # parse personal information
        tutor = Tutor()
        value: Union[str, int]
        for i, field in enumerate(fields):
            try:
                value = lines[i][1].strip()
            except IndexError:
                value = ""
            if value == "":
                if field == "phone":
                    value = "-"
                elif field == "unsure_about_second_week":
                    value = 0
                else:
                    raise invalid_entry(f"invalid entry: value of {field} is missing")
            if field in ("monthly_work_hours", "max_hours_without_break", "max_tutorials_without_break",
                         "knowledge", "unsure_about_second_week"):
                value = int(value)
            if field == "monthly_work_hours":
                if value not in [40, 41, 60, 80]:
                    raise invalid_entry(f"invalid entry: {value} monthly working hours")
            elif field == "knowledge":
                if value not in range(4):
                    raise invalid_entry(f"invalid entry: C knowledge is {value}, but should be between 0 and 3")
            setattr(tutor, field, value)

        # parse availability
        tutor.availability = {}
        for week_i, (week, days_of_week) in enumerate(sorted(days_by_week.items())):
            for time_i, time in enumerate(times):
                line_i = len(fields) + 3 + week_i * (len(times) + 3) + time_i
                line = lines[line_i][2:]

                if len(line) < len(days_of_week):
                    raise invalid_entry(f"invalid availablity ({tutor}): week {week_i} at {time}: too few entries")

                # iterate through all days of the same week and the same time
                for day, available_str in zip(days_of_week, line):
                    available: Optional[int]
                    if available_str == "X" or available_str.strip() == "":
                        available = None
                    else:
                        available = int(available_str)
                        if available not in range(4):
                            raise invalid_entry(f"invalid availablity ({tutor}): {day} at {time}: {available}, but should be between 0 and 3")

                    # validity check of available with respect to forbidden timeslots
                    if available is None:
                        if time not in settings.settings.forbidden_timeslots._or({})[day]._or([])():
                            if time != 14:
                                print(f"time: {time}")
                                # availability not set but expected
                                raise invalid_entry(f"invalid availablity ({tutor}): {day} at {time}: not set where it is expected")
                    else:
                        if time in settings.settings.forbidden_timeslots._or({})[day]._or([])():
                            # availability set but not expected
                            raise invalid_entry(f"invalid availablity ({tutor}): {day} at {time}: {available} where it is not expected")

                    tutor.availability.setdefault(day, {})[time] = available
                    tutor.availability.setdefault(day, {})[time+1] = available  # TODO
        return tutor

    @classmethod
    def load_from_file_second_week(cls, filename: str) -> "Tutor":
        fields = ("last_name",)

        # split days by week and load times
        days = cast(Sequence[datetime.date], settings.settings.days())
        days_by_week: Dict[Tuple[int, int], List[datetime.date]] = {}
        for day in days:
            days_by_week.setdefault(day.isocalendar()[:2], []).append(day)
        times = cast(Sequence[int], settings.settings.times())

        locale.resetlocale()  # fix missing locale bug
        lines: List[str]
        with open(filename) as f:
            dialect = csv.Sniffer().sniff(f.read(50).split("\n")[0])
            f.seek(0)
            reader = csv.reader(f, dialect)
            lines = list(reader)
        if len(lines) < len(fields) + (2 + len(times)):  # ignore first week
            raise ValueError(f"cannot parse {filename}: too few lines")

        def invalid_entry(message: str) -> ValueError:
            e = ValueError(message)
            e.tutor = tutor
            return e

        # parse personal information
        tutor = Tutor()
        for i, field in enumerate(fields):
            try:
                value = lines[i][1].strip()
            except IndexError:
                value = ""
            if value == "":
                raise invalid_entry(f"invalid entry: value of {field} is missing")
            setattr(tutor, field, value)

        # parse availability, ignore first week
        tutor.availability = {}
        for week_i, (week, days_of_week) in enumerate(sorted(days_by_week.items())[1:]):
            for time_i, time in enumerate(times):
                line_i = len(fields) + 2  + time_i
                line = lines[line_i][2:]

                if len(line) < len(days_of_week):
                    raise invalid_entry(f"invalid availablity ({tutor}): week {week_i} at {time}: too few entries")

                # iterate through all days of the same week and the same time
                for day, available_str in zip(days_of_week, line):
                    available: Optional[int]
                    if available_str == "X" or available_str.strip() == "":
                        available = None
                    else:
                        available = int(available_str)
                        if available not in range(4):
                            raise invalid_entry(f"invalid availablity ({tutor}): {day} at {time}: {available}, but should be between 0 and 3")

                    # validity check of available with respect to forbidden timeslots
                    if available is None:
                        if time not in settings.settings.forbidden_timeslots._or({})[day]._or([])():
                            # availability not set but expected
                            raise invalid_entry(f"invalid availablity ({tutor}): {day} at {time}: not set where it is expected")
                    else:

                        if time in settings.settings.forbidden_timeslots._or({})[day]._or([])():
                            # availability set but not expected
                            raise invalid_entry(f"invalid availablity ({tutor}): {day} at {time}: {available} where it is not expected")


                    tutor.availability.setdefault(day, {})[time] = available
                    tutor.availability.setdefault(day, {})[time+1] = available  # TODO
        return tutor


def load_tutors() -> Sequence[Tutor]:
    """
    Load tutors from tutor responses.
    """
    tutor_responses_paths = list(map(pathlib.Path, settings.settings.paths.tutor_responses()))

    tutors = {}  # type: Dict[str, Tutor]
    path = tutor_responses_paths[0]
    for file in path.glob("*.csv"):
        try:
            tutor = Tutor.load_from_file(str(file))
            tutors[tutor.last_name] = tutor
        except Exception as e:
            print("\033[1;31m", end="")
            print("Exception in file", file)
            print("\033[0;31m", end="")
            print(traceback.format_exc())
            if hasattr(e, "tutor"):
                print("Tutor:", e.tutor.first_name, e.tutor.last_name)
                print("Mail:", e.tutor.email if hasattr(e.tutor, "email") else None)
                print("Phone:", e.tutor.phone if hasattr(e.tutor, "phone") else None)
            print("\033[0m")

    # second week

    if len(tutor_responses_paths) > 1:
        names_of_tutors_not_updated = set([tutor.last_name for tutor in tutors.values()])
        path = tutor_responses_paths[1]
        for file in path.glob("*.csv"):
            try:
                tutor_week_2 = Tutor.load_from_file_second_week(str(file))
                tutor = tutors[tutor_week_2.last_name]
                tutor.availability.update(tutor_week_2.availability)
                print(f"successfully updated availability of tutor {tutor_week_2.last_name}")
                names_of_tutors_not_updated.remove(tutor_week_2.last_name)
            except Exception as e:
                print("\033[1;31m", end="")
                print("Exception in file", file)
                print("\033[0;31m", end="")
                print(traceback.format_exc())
                if hasattr(e, "tutor"):
                    print("Tutor:", e.tutor.first_name, e.tutor.last_name)
                    print("Mail:", e.tutor.email if hasattr(e.tutor, "email") else None)
                    print("Phone:", e.tutor.phone if hasattr(e.tutor, "phone") else None)
                print("\033[0m")

        if len(names_of_tutors_not_updated) > 0:
            print("\n\n\nWARNING WARNING WARNING!!!!")
            print(f"tutors not updated {names_of_tutors_not_updated}")

    return list(tutors.values())
