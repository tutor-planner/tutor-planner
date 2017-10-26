__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "to_single_hour_precision",
    "day_index_to_date",
    "date_to_day_index",
]

import copy
import datetime
from typing import List, Dict

from .settings import settings


def to_single_hour_precision(dictionary: Dict[int, Dict[int, List[str]]]) -> Dict[int, Dict[int, List[str]]]:
    """
    Convert dict to single hour precision.
    """
    single_hour = copy.deepcopy(dictionary)
    for day, value in dictionary.items():
        for hour, value2 in value.items():
            single_hour[day][hour + 1] = value2
    return single_hour


def day_index_to_date(day_index: int) -> datetime.date:
    """
    Convert day index to date.
    """
    return settings.days()[day_index - 1]


def date_to_day_index(date: datetime.date) -> int:
    """
    Convert date to day index.
    """
    return settings.days().index(date) + 1
