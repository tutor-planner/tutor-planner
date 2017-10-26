__author__ = ("Matthias Rost <mrost AT inet.tu-berlin.de>, "
              "Alexander Elvers <aelvers AT inet.tu-berlin.de>")

__all__ = [
    "Settings",
    "load_settings",
    "settings",
    "hours_real",
    "pre_hours_real",
    "get_room_info",
    "TUTORIUM",
    "UEBUNG_TEL",
    "UEBUNG_MAR",
    "KONTROLLE",
    "TASKS",
    "weekdays",
]

import re
from typing import Dict, Any, Iterable

import yaml


SETTINGS_FILE = "settings.yaml"
PLAN_PATHS_FILE = "plan_paths.yaml"


class Settings:
    """
    Settings wrapper

    Wraps the data so that it can be used easily.

    You can access dicts by using attribute or item syntax, lists by using item
    syntax. Additionally, you can use _get with a default value (similar to get
    of dicts) and _or for specifying a value that is used instead of None.

    To get the queried data, you have to call the whole construct.

    Example:

    >>> s = Settings([
    ...         {
    ...             "a": 1,
    ...             "b": "c",
    ...         }
    ... ], [
    ...     {
    ...         "a": 2,
    ...         "b": "d",
    ...     }
    ... ])
    >>> s[0].a()
    1
    """

    _data: Any
    _strict: bool

    def __init__(self, data: Any = None, strict: bool = False) -> None:
        """
        Create a wrapper object filled with data. When using strict mode, no
        default will be returned on missing items or type errors in __getitem__
        and __getattr__.
        """
        if isinstance(data, Settings):
            data = data._data
        self._data = data
        self._strict = strict

    def __getitem__(self, key: Any) -> "Settings":
        """
        Query data by using s[foo] syntax. Data has to exist if strict mode is
        used. Otherwise an empty settings wrapper is used.

        Returns a settings wrapper again.
        """
        try:
            return Settings(self._data[key], self._strict)
        except (TypeError, KeyError, IndexError) as e:
            if self._strict:
                raise
            return Settings(strict=self._strict)

    def __getattr__(self, key: str) -> "Settings":
        """
        Query data by using s.foo syntax. Data has to exist if strict mode is
        used. Otherwise an empty settings wrapper is used.

        Returns a settings wrapper again.
        """
        if key.startswith("__"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
        return self[key]

    def __call__(self) -> Any:
        """
        Unwrap the data.
        """
        return self._data

    def _or(self, other: Any) -> "Settings":
        """
        If data is None, returns a wrapped default value. Else, self is returned.

        >>> s = Settings({"a": 7})
        >>> s.a._or(5)()
        7
        >>> s.b._or(5)()
        5
        """
        if self._data is None:
            return Settings(other, self._strict)
        else:
            return self

    def _get(self, key: Any, default: Any = None) -> "Settings":
        """
        Query data similar to __getitem__, but uses a default value.

        In non-strict mode, the difference to __getitem__ combined with _or is
        that it returns the default only on missing items.
        """
        try:
            return Settings(self._data[key], self._strict)
        except (TypeError, KeyError, IndexError) as e:
            return Settings(default, strict=self._strict)


def load_settings(file: str = None) -> Settings:
    if file is None:
        file = SETTINGS_FILE
    with open(file) as f:
        # return yaml.safe_load(f)
        settings = Settings(yaml.safe_load(f))
        return settings


try:
    settings = load_settings()
except FileNotFoundError:
    settings = Settings()


precision = 1


def hours_real(d) -> Iterable[int]:
    """
    Hours of a day to plan.
    """
    lower, upper = 10, 18
    return range(lower, upper, precision)


def pre_hours_real(d) -> Iterable[int]:
    """
    Hours of a day to plan without the last hour.
    """
    return hours_real(d)[:-1]


DAYS = range(1, 11)


def get_room_info(room_name: str) -> Dict[str, Any]:
    """
    Get room information by room name.
    """
    room_type = None
    capacity = None
    tutorial_size = None
    projector = None
    room_patterns = settings.room_patterns() or []
    for room_pattern in room_patterns:
        pattern = room_pattern.get("pattern", "*")
        regex = re.compile("^{}$".format(".*".join(map(re.escape, pattern.split("*")))), re.IGNORECASE)
        if regex.match(room_name):
            if "type" in room_pattern:
                room_type = room_pattern["type"]
            if "capacity" in room_pattern:
                capacity = room_pattern["capacity"]
            if "tutorial_size" in room_pattern:
                tutorial_size = room_pattern["tutorial_size"]
            if "projector" in room_pattern:
                projector = bool(room_pattern["projector"])
    return dict(type=room_type, capacity=capacity, projector=projector, tutorial_size=tutorial_size)


TUTORIUM = "Tutorium"
UEBUNG_MAR = "RechneruebungMAR"
UEBUNG_TEL = "RechneruebungTEL"
KONTROLLE = "Kontrolle"

TASKS = TUTORIUM, UEBUNG_TEL, UEBUNG_MAR, KONTROLLE


weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
